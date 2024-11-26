import os
from typing import Any, Dict, List, Optional

from config import DATABASE_CONFIG
from models.base import db_connection

from .schema_versions import SCHEMA_VERSIONS


class SchemaManager:
    """数据库表结构管理器

    负责管理数据库的版本迁移，包括：
    - 版本管理：获取当前版本、最新版本
    - 表结构迁移：创建、修改、删除表
    - 数据迁移：在表结构变更时保持数据完整性
    - 结构验证：确保迁移后的数据库结构符合预期
    """

    def __init__(self):
        self.versions = SCHEMA_VERSIONS

    def get_current_version(self, db_path: Optional[str] = None) -> int:
        """从数据库文件名获取当前版本

        Args:
            db_path: 数据库文件路径，如果为None则使用配置中的路径

        Returns:
            int: 当前数据库版本号，如果无法获取则返回0
        """
        path = db_path or DATABASE_CONFIG["path"]
        if not os.path.exists(path):
            return 0

        filename = os.path.basename(path)
        try:
            version_str = filename.split(".v")[1].split(".")[0]
            return int(version_str)
        except (IndexError, ValueError):
            return 0

    def migrate_to_version(
        self, target_version: int, original_version: Optional[int] = None, db_name: str = "main"
    ) -> bool:
        """迁移到指定版本

        Args:
            target_version: 目标版本号
            original_version: 原始版本号，如果为None则自动获取
            db_name: 数据库名称

        Returns:
            bool: 迁移是否成功
        """
        current_version = (
            original_version
            if original_version is not None
            else self.get_current_version(DATABASE_CONFIG["paths"][db_name])
        )

        print(f"开始迁移数据库[{db_name}]: 当前版本 {current_version} -> 目标版本 {target_version}")
        print(f"使用数据库: {DATABASE_CONFIG['paths'][db_name]}")

        try:
            with db_connection(db_name=db_name) as db:
                with db.atomic():
                    self._execute_migration(current_version, target_version, db, db_name)
                    self.validate_database(db, target_version, db_name)
                    return True
        except Exception as e:
            print(f"迁移失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _execute_migration(self, current_version: int, target_version: int, db, db_name: str):
        """执行版本迁移"""
        if current_version < target_version:
            self._migrate_up(current_version, target_version, db, db_name)
        else:
            self._migrate_down(current_version, target_version, db, db_name)
        print("\n迁移完成")

    def _migrate_up(self, current_version: int, target_version: int, db, db_name: str):
        """升级到更高版本"""
        for version in range(current_version + 1, target_version + 1):
            if version in self.versions:
                print(f"\n执行版本 {version} 的迁移...")
                self._apply_version(version, db, db_name)
                print(f"版本 {version} 迁移完成")

    def _migrate_down(self, current_version: int, target_version: int, db, db_name: str):
        """回滚到更低版本"""
        for version in range(current_version, target_version, -1):
            if version in self.versions:
                print(f"\n执行版本 {version} 的回滚...")
                self._revert_version(version, db, db_name)
                print(f"版本 {version} 回滚完成")

    def _apply_version(self, version: int, db, db_name: str):
        """应用指定版本的变更"""
        version_info = self.versions[version]
        print(f"升级到版本 {version}: {version_info['description']}")

        try:
            # 确保changes字段存在
            if "changes" not in version_info:
                version_info["changes"] = {}

            # 确保必需的子字段存在
            changes = version_info["changes"]
            if "new_tables" not in changes:
                changes["new_tables"] = []
            if "alter_tables" not in changes:
                changes["alter_tables"] = {}
            if "drop_tables" not in changes:
                changes["drop_tables"] = []

            # 1. 处理表重命名
            self._handle_table_renames(version_info, db, db_name)

            # 2. 处理新表创建
            self._handle_new_tables(version_info, db, db_name)

            # 3. 处理表修改
            self._handle_table_modifications(version_info, db, db_name)

            # 4. 处理表删除
            self._handle_table_drops(version_info, db, db_name)

            print(f"\n版本 {version} 的所有变更已应用")
        except Exception as e:
            print(f"应用版本 {version} 失败: {e}")
            raise e

    def _handle_table_renames(self, version_info: Dict[str, Any], db, db_name: str):
        """处理表重命名操作"""
        for table_name, changes in version_info["changes"]["alter_tables"].items():
            if "rename_to" in changes:
                new_table_name = changes["rename_to"]
                print(f"\n重命名表: {table_name} -> {new_table_name}")
                sql = f"ALTER TABLE {table_name} RENAME TO {new_table_name}"
                db.execute_sql(sql)

    def _handle_new_tables(self, version_info: Dict[str, Any], db, db_name: str):
        """处理新表创建"""
        for table_name in version_info["changes"]["new_tables"]:
            table_info = version_info["schema"][table_name]
            print(f"\n创建新表: {table_name}")
            self._create_table(table_name, table_info, db, db_name)

    def _handle_table_modifications(self, version_info: Dict[str, Any], db, db_name: str):
        """处理表修改"""
        for table_name, changes in version_info["changes"]["alter_tables"].items():
            if "rename_to" in changes:
                new_table_name = changes["rename_to"]
                if new_table_name in version_info["schema"]:
                    print(f"\n修改表: {new_table_name}")
                    self._rebuild_table(
                        new_table_name,
                        version_info["schema"][new_table_name],
                        changes,
                        db,
                        db_name,
                    )
            else:
                print(f"\n修改表: {table_name}")
                self._rebuild_table(
                    table_name,
                    version_info["schema"][table_name],
                    changes,
                    db,
                    db_name,
                )

    def _handle_table_drops(self, version_info: Dict[str, Any], db, db_name: str):
        """处理表删除"""
        # 获取drop_tables列表，如果不存在则使用空列表
        drop_tables = version_info.get("changes", {}).get("drop_tables", [])

        for table_name in drop_tables:
            print(f"\n删除表: {table_name}")
            self._drop_table(table_name, db, db_name)

    def _create_table(self, table_name: str, table_info: Dict[str, Any], db, db_name: str):
        """创建表

        Args:
            table_name: 表名
            table_info: 表结构信息
            db: 数据库连接
        """
        try:
            # 检查表是否已存在
            if self._table_exists(table_name, db, db_name):
                print(f"表 {table_name} 已存在，跳过创建")
                return

            # 构建字段定义
            field_defs = self._build_field_definitions(table_info)

            # 创建表
            sql = f"CREATE TABLE {table_name} ({', '.join(field_defs)})"
            print(f"执行SQL: {sql}")
            db.execute_sql(sql)

            # 创建索引
            self._create_indexes(table_name, table_info, db, db_name)

            print(f"表 {table_name} 创建成功")

        except Exception as e:
            print(f"创建表 {table_name} 失败: {e}")
            raise e

    def _table_exists(self, table_name: str, db, db_name: str) -> bool:
        """检查表是否存在"""
        cursor = db.execute_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return cursor.fetchone() is not None

    def _build_field_definitions(self, table_info: Dict[str, Any]) -> List[str]:
        """构建字段定义列表"""
        field_defs = [f"{name} {type_}" for name, type_ in table_info["fields"].items()]

        # 添加主键约束
        if "primary_key" in table_info:
            pk_fields = ", ".join(table_info["primary_key"])
            field_defs.append(f"PRIMARY KEY ({pk_fields})")

        # 添加外键约束
        if "foreign_keys" in table_info:
            for field, reference in table_info["foreign_keys"].items():
                field_defs.append(f"FOREIGN KEY ({field}) REFERENCES {reference}")

        return field_defs

    def _create_indexes(self, table_name: str, table_info: Dict[str, Any], db, db_name: str):
        """创建表索引"""
        if "indexes" in table_info:
            for index_field in table_info["indexes"]:
                index_name = f"{table_name}_{index_field}"
                sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({index_field})"
                print(f"执行SQL: {sql}")
                db.execute_sql(sql)

    def _rebuild_table(
        self, table_name: str, new_schema: Dict[str, Any], changes: Dict[str, Any], db, db_name: str
    ):
        """重建表（用于SQLite不支持的ALTER TABLE操作）"""
        print(f"重建表 {table_name}")

        try:
            # 1. 重命名原表为临时表
            temp_table = f"{table_name}_old"
            db.execute_sql(f"ALTER TABLE {table_name} RENAME TO {temp_table}")

            # 2. 使用新结构创建表
            self._create_table(table_name, new_schema, db, db_name)

            # 3. 获取需要迁移的字段
            common_fields = self._get_common_fields(temp_table, new_schema["fields"], db)

            # 4. 处理字段映射
            data_migration = changes.get("data_migration", {})
            field_defaults = changes.get("field_defaults", {})
            rename_columns = changes.get("rename_columns", {})

            select_fields = []
            insert_fields = []

            # 处理所有新表字段
            for new_field in new_schema["fields"].keys():
                if new_field in data_migration:
                    # 字段被重命名（通过data_migration）
                    select_fields.append(data_migration[new_field])
                    insert_fields.append(new_field)
                elif new_field in rename_columns.values():
                    # 字段被重命名（通过rename_columns）
                    old_field = [k for k, v in rename_columns.items() if v == new_field][0]
                    select_fields.append(old_field)
                    insert_fields.append(new_field)
                elif new_field in common_fields:
                    # 字段名称未变
                    select_fields.append(new_field)
                    insert_fields.append(new_field)
                elif new_field in field_defaults:
                    # 新字段有默认值
                    select_fields.append(f"'{field_defaults[new_field]}' as {new_field}")
                    insert_fields.append(new_field)
                else:
                    # 检查是否为NOT NULL字段
                    is_not_null = False
                    for field_def in new_schema["fields"][new_field].split():
                        if field_def.upper() == "NOT" and "NULL" in field_def.upper():
                            is_not_null = True
                            break

                    if is_not_null:
                        # 对于NOT NULL字段，需要提供默认值
                        field_type = new_schema["fields"][new_field].split()[0].upper()
                        if "VARCHAR" in field_type or "TEXT" in field_type:
                            select_fields.append(f"'' as {new_field}")
                        elif "INT" in field_type or "DECIMAL" in field_type:
                            select_fields.append(f"0 as {new_field}")
                        elif "DATE" in field_type:
                            select_fields.append(f"CURRENT_DATE as {new_field}")
                        elif "DATETIME" in field_type:
                            select_fields.append(f"CURRENT_TIMESTAMP as {new_field}")
                        else:
                            select_fields.append(f"NULL as {new_field}")
                        insert_fields.append(new_field)

            # 5. 迁移数据
            if select_fields and insert_fields:
                insert_fields_str = ", ".join(insert_fields)
                select_fields_str = ", ".join(select_fields)
                sql = f"INSERT INTO {table_name} ({insert_fields_str}) SELECT {select_fields_str} FROM {temp_table}"
                print(f"执行SQL: {sql}")
                db.execute_sql(sql)

            # 6. 删除临时表
            db.execute_sql(f"DROP TABLE {temp_table}")

            print(f"表 {table_name} 重建完成")

        except Exception as e:
            print(f"重建表 {table_name} 失败: {e}")
            # 回滚操作：删除新表，恢复旧表
            try:
                db.execute_sql(f"DROP TABLE IF EXISTS {table_name}")
                db.execute_sql(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
            except Exception as rollback_error:
                print(f"回滚失败: {rollback_error}")
            raise e

    def _get_common_fields(
        self, table_name: str, new_fields: Dict[str, str], db
    ) -> List[str]:
        """获取两个表结构中的共同字段"""
        cursor = db.execute_sql(f"PRAGMA table_info({table_name})")
        old_fields = [row[1] for row in cursor.fetchall()]
        return [field for field in old_fields if field in new_fields]

    def _drop_table(self, table_name: str, db, db_name: str):
        """删除表"""
        db.execute_sql(f"DROP TABLE IF EXISTS {table_name}")

    def validate_database(self, db, target_version: int, db_name: str):
        """验证数据库结构是否符合预期"""
        print(f"\n开始验证数据库[{db_name}]结构...")
        version = self.versions[target_version]
        for table_name, table_info in version["schema"].items():
            # 检查表是否属于当前数据库
            if table_info.get("db_name", "main") != db_name:
                continue

            try:
                cursor = db.execute_sql(f"PRAGMA table_info({table_name})")
                existing_fields = {row[1] for row in cursor.fetchall()}
                expected_fields = set(table_info["fields"].keys())

                if existing_fields != expected_fields:
                    message = f"表 {table_name} 的字段不匹配"
                    print(message)
                    print(f"现有字段: {existing_fields}")
                    print(f"预期字段: {expected_fields}")
                    raise Exception(message)
                else:
                    print(f"表 {table_name} 验证通过")

            except Exception as e:
                print(f"验证表 {table_name} 失败: {e}")
                raise e
