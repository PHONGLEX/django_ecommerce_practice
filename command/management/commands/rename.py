from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = "Rename a django project"
    
    def add_arguments(self, parser) -> None:
        parser.add_argument("old_project_name", type=str, help="The old Django project name")
        parser.add_argument("new_project_name", type=str, help="The new Django project name")
        return super().add_arguments(parser)
    
    def handle(self, *args, **kwargs):
        new_project_name = kwargs['new_project_name']
        old_project_name = kwargs['old_project_name']
        
        files_to_rename = [f'{old_project_name}/settings/base.py', f'{old_project_name}/wsgi.py', f'{old_project_name}/asgi.py', 'manage.py']
        folder_to_rename = old_project_name
        
        for f in files_to_rename:
            with open(f, 'r') as file:
                filedata = file.read()
                
            filedata = filedata.replace(old_project_name, new_project_name)
            
            with open(f, 'w') as file:
                file.write(filedata)
                
        os.rename(folder_to_rename, new_project_name)
        
        self.stdout.write(self.style.SUCCESS('Project has been rename to %s' % new_project_name))