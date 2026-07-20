"""Filesystem helpers used by project routes and services."""

import os
import shutil
import stat

from app.config import Config


def should_skip_directory(dirname):
    return (
        dirname in Config.IGNORED_DIRECTORIES
        or dirname.startswith(".")
        or dirname.startswith("__")
    )


def should_skip_file(filename):
    return (
        filename.startswith(".")
        or filename.startswith("__")
        or filename.endswith(Config.IGNORED_FILE_SUFFIXES)
    )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.SUPPORTED_EXTENSIONS


def force_delete_file(file_path):
    """Force delete a file by removing its read-only attribute."""
    try:
        if os.path.exists(file_path):
            os.chmod(file_path, stat.S_IWRITE)
            os.remove(file_path)
            return True
    except OSError:
        return False
    return False


def remove_empty_folders(folder_path, upload_folder):
    """Remove empty folders recursively, retaining the configured upload root."""
    try:
        root_path = os.path.abspath(folder_path)
        upload_root = os.path.abspath(upload_folder)
        for root, dirs, _ in os.walk(folder_path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if os.path.exists(dir_path) and not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except OSError:
                    pass
            try:
                current_root = os.path.abspath(root)
                if current_root not in {upload_root, root_path} and os.path.exists(root) and not os.listdir(root):
                    os.rmdir(root)
            except OSError:
                pass
        if root_path != upload_root and os.path.exists(folder_path) and not os.listdir(folder_path):
            os.rmdir(folder_path)
    except OSError:
        pass


def force_delete_folder(folder_path):
    """Force delete a folder and its contents, preserving legacy return semantics."""
    if not os.path.exists(folder_path):
        return True
    try:
        shutil.rmtree(folder_path, ignore_errors=True)
        return True
    except OSError:
        try:
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    force_delete_file(os.path.join(root, filename))
            shutil.rmtree(folder_path, ignore_errors=True)
            return True
        except OSError:
            return False
