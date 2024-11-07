from typing import Optional
import os
import shutil
from migrations.version_manager import SchemaManager
from config import DATABASE_CONFIG
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
        current_version = version_manager.get_current_version()
        latest_version = max(version_manager.versions.keys())

        print(f"当前数据库版本: {current_version}")
        print(f"最新数据库版本: {latest_version}")

        if current_version == latest_version and os.path.exists(
            DATABASE_CONFIG["path"]
        ):
            print("数据库已经是最新版本")
            return True

        # 构建新的数据库文件路径
        new_db_path = get_new_db_path(latest_version)

        # 如果存在旧的迁移文件，先删除
        if os.path.exists(new_db_path):
            os.remove(new_db_path)
            print(f"删除旧的迁移文件: {new_db_path}")

        # 备份当前配置
        old_db_path = DATABASE_CONFIG["path"]

        try:
            # 如果存在当前数据库文件，则复制
            if os.path.exists(old_db_path):
                shutil.copy2(old_db_path, new_db_path)
                print(f"创建数据库副本: {new_db_path}")

            # 临时更新配置指向新数据库文件
            DATABASE_CONFIG["path"] = new_db_path
            # 重新初始化数据库连接
            init_db(new_db_path)

            # 执行迁移（使用原始版本号）
            if version_manager.migrate_to_version(latest_version, current_version):
                print(f"数据库已成功迁移到版本 {latest_version}")
                print(f"新的数据库文件: {new_db_path}")
                print("\n请更新配置文件中的数据库路径:")
                print(f'DATABASE_CONFIG["path"] = "{new_db_path}"')
                return True
            else:
                # 迁移失败，恢复配置和数据库连接
                DATABASE_CONFIG["path"] = old_db_path
                init_db(old_db_path)
                if os.path.exists(new_db_path):
                    os.remove(new_db_path)
                    print(f"迁移失败，已删除新数据库文件: {new_db_path}")
                return False

        except Exception as e:
            print(f"迁移过程中出错: {e}")
            # 恢复配置和数据库连接
            DATABASE_CONFIG["path"] = old_db_path
            init_db(old_db_path)
            if os.path.exists(new_db_path):
                os.remove(new_db_path)
                print(f"迁移失败，已删除新数据库文件: {new_db_path}")
            raise e

    except Exception as e:
        print(f"数据库迁移失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def get_new_db_path(version: int) -> str:
    """获取新版本数据库文件路径"""
    db_dir = ensure_db_dir()
    current_path = DATABASE_CONFIG["path"]
    basename = os.path.basename(current_path)

    # 从当前文件名中提取基础名称（移除版本号）
    base_name = (
        basename.split(".v")[0] if ".v" in basename else basename.split(".db")[0]
    )

    # 构建新的文件名
    return os.path.join(db_dir, f"{base_name}.v{version}.db")


if __name__ == "__main__":
    migrate_database()
