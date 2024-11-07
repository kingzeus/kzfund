import os
from typing import Dict, Any, List, Optional
from models.base import db_connection, init_db
from .schema_versions import SCHEMA_VERSIONS
from config import DATABASE_CONFIG


class SchemaManager:
    """数据库表结构管理器"""

    def __init__(self):
        self.versions = SCHEMA_VERSIONS

    def get_current_version(self, db_path: Optional[str] = None) -> int:
        """从数据库文件名获取当前版本"""
        path = db_path or DATABASE_CONFIG["path"]
        if not os.path.exists(path):
            return 0

        filename = os.path.basename(path)
        try:
            version_str = filename.split(".v")[1].split(".")[0]
            return int(version_str)
        except (IndexError, ValueError):
            return 0

    def get_latest_version(self) -> int:
        """获取最新版本号"""
        return max(self.versions.keys())

    def get_version_info(self, version: int) -> Dict[str, Any]:
        """获取指定版本的信息"""
        return self.versions.get(version, {})

    def migrate_to_version(
        self, target_version: int, original_version: Optional[int] = None
    ) -> bool:
        """迁移到指定版本"""
        current_version = (
            original_version
            if original_version is not None
            else self.get_current_version()
        )

        print(f"开始迁移: 当前版本 {current_version} -> 目标版本 {target_version}")

        try:
            print(f"使用数据库: {DATABASE_CONFIG['path']}")

            with db_connection(DATABASE_CONFIG["path"]) as db:
                with db.atomic():
                    if current_version < target_version:
                        for version in range(current_version + 1, target_version + 1):
                            if version in self.versions:
                                print(f"\n执行版本 {version} 的迁移...")
                                self._apply_version(version, db)
                                print(f"版本 {version} 迁移完成")
                    else:
                        for version in range(current_version, target_version, -1):
                            if version in self.versions:
                                print(f"\n执行版本 {version} 的回滚...")
                                self._revert_version(version, db)
                                print(f"版本 {version} 回滚完成")

                print("\n迁移完成")
                self.validate_database(db)  # 在迁移完成后验证数据库结构
                return True

        except Exception as e:
            print(f"迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _apply_version(self, version: int, db):
        """应用指定版本的变更"""
        version_info = self.versions[version]
        print(f"升级到版本 {version}: {version_info['description']}")
        print(f"使用数据库: {DATABASE_CONFIG['path']}")
        print(f"使用数据库: {db.database}")
        try:
            for table_name in version_info["changes"]["new_tables"]:
                table_info = version_info["schema"][table_name]
                print(f"\n创建新表: {table_name}")
                self._create_table(table_name, table_info, db)

            for table_name, changes in version_info["changes"]["alter_tables"].items():
                print(f"\n修改表: {table_name}")
                self._rebuild_table(table_name, version_info["schema"][table_name], db)

            for table_name in version_info["changes"]["drop_tables"]:
                print(f"\n删除表: {table_name}")
                self._drop_table(table_name, db)

            print(f"\n版本 {version} 的所有变更已应用")

        except Exception as e:
            print(f"应用版本 {version} 失败: {e}")
            raise e

    def _create_table(self, table_name: str, table_info: Dict[str, Any], db):
        """创建表"""
        try:
            cursor = db.execute_sql(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            if cursor.fetchone():
                print(f"表 {table_name} 已存在，跳过创建")
                return

            fields = table_info["fields"]
            field_defs = [f"{name} {type_}" for name, type_ in fields.items()]

            if "primary_key" in table_info:
                pk_fields = ", ".join(table_info["primary_key"])
                field_defs.append(f"PRIMARY KEY ({pk_fields})")

            if "foreign_keys" in table_info:
                for field, reference in table_info["foreign_keys"].items():
                    field_defs.append(f"FOREIGN KEY ({field}) REFERENCES {reference}")

            sql = f"CREATE TABLE {table_name} ({', '.join(field_defs)})"
            print(f"执行SQL: {sql}")
            db.execute_sql(sql)

            if "indexes" in table_info:
                for index_field in table_info["indexes"]:
                    index_name = f"{table_name}_{index_field}"
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({index_field})"
                    print(f"执行SQL: {sql}")
                    db.execute_sql(sql)

            print(f"表 {table_name} 创建成功")

        except Exception as e:
            print(f"创建表 {table_name} 失败: {e}")
            raise e

    def _rebuild_table(self, table_name: str, new_schema: Dict[str, Any], db):
        """重建表（用于SQLite不支持的ALTER TABLE操作）"""
        print(f"重建表 {table_name}")

        try:
            temp_table = f"{table_name}_old"
            sql = f"ALTER TABLE {table_name} RENAME TO {temp_table}"
            print(f"执行SQL: {sql}")
            db.execute_sql(sql)

            self._create_table(table_name, new_schema, db)

            common_fields = self._get_common_fields(
                temp_table, new_schema["fields"], db
            )
            if common_fields:
                fields_str = ", ".join(common_fields)
                sql = f"INSERT INTO {table_name} ({fields_str}) SELECT {fields_str} FROM {temp_table}"
                print(f"执行SQL: {sql}")
                db.execute_sql(sql)

            sql = f"DROP TABLE {temp_table}"
            print(f"执行SQL: {sql}")
            db.execute_sql(sql)

            print(f"表 {table_name} 重建完成")

        except Exception as e:
            print(f"重建表 {table_name} 失败: {e}")
            raise e

    def _get_common_fields(
        self, table_name: str, new_fields: Dict[str, str], db
    ) -> List[str]:
        """获取两个表结构中的共同字段"""
        sql = f"PRAGMA table_info({table_name})"
        cursor = db.execute_sql(sql)
        old_fields = [row[1] for row in cursor.fetchall()]
        return [field for field in old_fields if field in new_fields]

    def _drop_table(self, table_name: str, db):
        """删除表"""
        sql = f"DROP TABLE IF EXISTS {table_name}"
        print(f"执行SQL: {sql}")
        db.execute_sql(sql)

    def _revert_table_changes(self, table_name: str, changes: Dict[str, Any], db):
        """回滚表的修改"""
        pass

    def validate_database(self, db):
        """验证数据库结构是否符合预期"""
        print("\n开始验证数据库结构...")
        for version in self.versions.values():
            for table_name, table_info in version["schema"].items():
                try:
                    cursor = db.execute_sql(f"PRAGMA table_info({table_name})")
                    existing_fields = {row[1] for row in cursor.fetchall()}
                    expected_fields = set(table_info["fields"].keys())

                    if existing_fields != expected_fields:
                        print(f"表 {table_name} 的字段不匹配")
                        print(f"现有字段: {existing_fields}")
                        print(f"预期字段: {expected_fields}")
                    else:
                        print(f"表 {table_name} 验证通过")

                except Exception as e:
                    print(f"验证表 {table_name} 失败: {e}")
