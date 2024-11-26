import os
import shutil
from typing import Dict

from config import DATABASE_CONFIG
from migrations.version_manager import SchemaManager
from models.base import init_db


def ensure_db_dir():
    """确保数据库目录存在"""
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"创建数据库目录: {db_dir}")
    return db_dir


def migrate_database():
    """执行数据库迁移"""
    try:
        print("开始数据库迁移...")

        # 确保数据库目录存在
        ensure_db_dir()

        # 初始化版本管理器
        version_manager = SchemaManager()

        # 获取当前版本和目标版本
        current_versions = {
            db_name: version_manager.get_current_version(db_path)
            for db_name, db_path in DATABASE_CONFIG["paths"].items()
        }
        latest_version = max(version_manager.versions.keys())

        print("当前数据库版本:")
        for db_name, version in current_versions.items():
            print(f"  {db_name}: {version}")
        print(f"最新数据库版本: {latest_version}")

        # 检查是否需要迁移
        if all(v == latest_version for v in current_versions.values()) and all(
            os.path.exists(path) for path in DATABASE_CONFIG["paths"].values()
        ):
            print("所有数据库已经是最新版本")
            return True

        # 构建新的数据库文件路径
        new_db_paths = {
            db_name: get_new_db_path(db_name, latest_version)
            for db_name in DATABASE_CONFIG["paths"].keys()
        }

        # 删除旧的迁移文件
        for db_path in new_db_paths.values():
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"删除旧的迁移文件: {db_path}")

        # 备份当前配置
        old_db_paths = DATABASE_CONFIG["paths"].copy()

        try:
            # 复制现有数据库文件
            for db_name, old_path in old_db_paths.items():
                if os.path.exists(old_path):
                    shutil.copy2(old_path, new_db_paths[db_name])
                    print(f"创建数据库副本: {new_db_paths[db_name]}")

            # 临时更新配置指向新数据库文件
            DATABASE_CONFIG["paths"].update(new_db_paths)
            # 重新初始化数据库连接
            init_db(new_db_paths)

            # 执行迁移
            success = True
            for db_name, current_version in current_versions.items():
                print(f"\n迁移数据库 {db_name}...")
                if not version_manager.migrate_to_version(latest_version, current_version, db_name):
                    success = False
                    break

            if success:
                print(f"\n所有数据库已成功迁移到版本 {latest_version}")
                print("\n新的数据库文件:")
                for db_name, path in new_db_paths.items():
                    print(f"  {db_name}: {path}")
                print("\n请更新配置文件中的数据库路径:")
                print('DATABASE_CONFIG["paths"] = {')
                for db_name, path in new_db_paths.items():
                    print(f'    "{db_name}": "{path}",')
                print("}")
                return True
            else:
                # 迁移失败，恢复配置和数据库连接
                DATABASE_CONFIG["paths"] = old_db_paths
                init_db(old_db_paths)
                for path in new_db_paths.values():
                    if os.path.exists(path):
                        os.remove(path)
                        print(f"迁移失败，已删除新数据库文件: {path}")
                return False

        except Exception as e:
            print(f"迁移过程中出错: {e}")
            # 恢复配置和数据库连接
            DATABASE_CONFIG["paths"] = old_db_paths
            init_db(old_db_paths)
            for path in new_db_paths.values():
                if os.path.exists(path):
                    os.remove(path)
                    print(f"迁移失败，已删除新数据库文件: {path}")
            raise e

    except Exception as e:
        print(f"数据库迁移失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def get_new_db_path(db_name: str, version: int) -> str:
    """获取新版本数据库文件路径"""
    db_dir = ensure_db_dir()
    current_path = DATABASE_CONFIG["paths"][db_name]
    basename = os.path.basename(current_path)

    # 从当前文件名中提取基础名称（移除版本号）
    base_name = (
        basename.split(".v")[0] if ".v" in basename else basename.split(".db")[0]
    )

    # 构建新的文件名
    return os.path.join(db_dir, f"{base_name}.v{version}.db")


if __name__ == "__main__":
    migrate_database()
