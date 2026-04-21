import re
from app import db
from app.models.models import Dependency, File

class DependencyService:
    def build_dependency_graph(self):
        # Clear old dependencies
        Dependency.query.delete()
        
        files = File.query.all()
        # Use a map for O(1) lookup
        file_list = [f.filename for f in files]
        
        dep_count = 0
        MAX_DEPS = 1000 # Safety limit
        
        for file in files:
            if dep_count >= MAX_DEPS:
                print("Reached maximum dependency limit, stopping.")
                break
                
            content = file.content
            imports = set()
            
            # Python patterns
            if file.filetype == '.py':
                py_matches = re.findall(r'^(?:from|import)\s+([\w\.]+)', content, re.MULTILINE)
                imports.update(py_matches)
                
            # JS/TS patterns
            elif file.filetype in ['.js', '.ts']:
                js_matches = re.findall(r'(?:import|require)\s*\(?[\'\"]([\w\.\-\/]+)[\'\"]', content)
                imports.update(js_matches)
                
            for imp in imports:
                # Optimized matching: Check if import name exists in any filename
                # We prioritize exact matches or "imp in filename"
                for target_name in file_list:
                    if imp in target_name: 
                        dep = Dependency(parent_file=file.filename, child_file=target_name)
                        db.session.add(dep)
                        dep_count += 1
                        break
                        
        db.session.commit()
        print(f"Dependency graph built with {dep_count} links.")
        
    def get_dependencies(self):
        return Dependency.query.all()
