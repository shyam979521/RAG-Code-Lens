"""Project filesystem queries shared by page and API routes."""

import os

from app.utils.filesystem import should_skip_directory, should_skip_file


class ProjectService:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder

    def list_projects(self, include_details=False):
        projects = []
        if not os.path.exists(self.upload_folder):
            return projects

        for item in os.listdir(self.upload_folder):
            item_path = os.path.join(self.upload_folder, item)
            if not os.path.isdir(item_path):
                continue
            files = self._list_files(item_path, include_details)
            if files:
                projects.append({"name": item, "file_count": len(files), "files": files})
        return projects

    def list_all_project_files(self):
        all_files = []
        for project in self.list_projects():
            for file_data in project["files"]:
                all_files.append({
                    "name": file_data["name"],
                    "project": project["name"],
                    "description": f"File in {project['name']} project",
                })
        return all_files

    def get_workspace(self, project_name, selected_file=None):
        """Return read-only workspace data for one extracted project."""
        project_path = os.path.join(self.upload_folder, project_name)
        if not os.path.isdir(project_path):
            return None

        files = self._list_files(project_path, include_details=True)
        tree = {}
        languages = set()
        total_size = 0
        for file_data in files:
            total_size += file_data["size"]
            extension = file_data["extension"].lower()
            if extension not in {"txt", ""}:
                languages.add(extension.upper())
            node = tree
            path_parts = file_data["path"].replace("\\", "/").split("/")
            for part in path_parts[:-1]:
                node = node.setdefault(part, {})
            node.setdefault("__files__", []).append(file_data)

        selected = self._read_workspace_file(project_path, selected_file) if selected_file else None
        return {
            "name": project_name,
            "files": files,
            "tree": tree,
            "file_count": len(files),
            "total_size": total_size,
            "languages": sorted(languages)[:8],
            "selected": selected,
        }

    @staticmethod
    def _read_workspace_file(project_path, relative_path):
        if not relative_path:
            return None
        candidate = os.path.abspath(os.path.join(project_path, relative_path))
        root = os.path.abspath(project_path)
        if os.path.commonpath([candidate, root]) != root or not os.path.isfile(candidate):
            return None
        try:
            with open(candidate, "r", encoding="utf-8", errors="ignore") as source_file:
                return {
                    "path": relative_path,
                    "name": os.path.basename(relative_path),
                    "extension": os.path.splitext(relative_path)[1].lstrip(".").upper() or "TEXT",
                    "content": source_file.read(),
                }
        except OSError:
            return None

    def _list_files(self, project_path, include_details):
        files = []
        for root, dirs, filenames in os.walk(project_path):
            dirs[:] = [directory for directory in dirs if not should_skip_directory(directory)]
            for filename in filenames:
                if should_skip_file(filename):
                    continue
                try:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, project_path)
                    data = {"name": filename, "path": relative_path, "size": os.path.getsize(file_path)}
                    if include_details:
                        data.update({
                            "extension": filename.split(".")[-1] if "." in filename else "txt",
                            "folder": os.path.dirname(relative_path) or "root",
                        })
                    files.append(data)
                except OSError:
                    continue
        if include_details:
            files.sort(key=lambda item: item["name"])
        return files
