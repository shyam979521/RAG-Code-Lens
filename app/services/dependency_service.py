import re
from app import db
from app.models.models import Dependency, File

class DependencyService:
    def build_dependency_graph(self, project_name=None):
        # Clear dependencies for this project or all
        if project_name:
            Dependency.query.filter_by(project_name=project_name).delete()
            files = File.query.filter_by(project_name=project_name).all()
        else:
            Dependency.query.delete()
            files = File.query.all()
            
        # Use a map for O(1) lookup within the project or overall
        file_list = [f.filename for f in files]
        
        dep_count = 0
        MAX_DEPS = 5000 # Safety limit
        
        for file in files:
            if dep_count >= MAX_DEPS:
                print("Reached maximum dependency limit, stopping.")
                break
                
            content = file.content if file.content else ""
            imports = set()
            
            # Python patterns
            if file.filetype == '.py':
                # Improved regex to handle indented imports
                py_matches = re.findall(r'^\s*(?:from|import)\s+([\w\.]+)', content, re.MULTILINE)
                imports.update(py_matches)
                
            # JS/TS patterns
            elif file.filetype in ['.js', '.ts']:
                js_matches = re.findall(r'(?:import|require)\s*\(?[\'\"]([\w\.\-\/]+)[\'\"]', content)
                imports.update(js_matches)
                
            for imp in imports:
                # Optimized matching: Check if import name exists in any filename
                for target_name in file_list:
                    if imp in target_name: 
                        dep = Dependency(
                            parent_file=file.filename, 
                            child_file=target_name,
                            project_name=file.project_name
                        )
                        db.session.add(dep)
                        dep_count += 1
                        break
                        
        db.session.commit()
        print(f"Dependency graph built with {dep_count} links.")
        
    def get_dependencies(self, project_name=None):
        if project_name:
            return Dependency.query.filter_by(project_name=project_name).all()
        return Dependency.query.all()
