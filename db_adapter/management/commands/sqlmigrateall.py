import os, errno
import progressbar

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.migrations.loader import MigrationLoader
from django.db import DEFAULT_DB_ALIAS, connections


class Command(BaseCommand):
    out_folder_default = 'sqlmigrations'
    command_sucessfull_finish = 'Command finished! SQL scripts sucessfully saved into %s'

    def add_arguments(self, parser):
        # Positional aarguments
        parser.add_argument('out_folder', type=str, default='.')

        # Optional arguments
        parser.add_argument(
            '--no-folder-per-app',
            action='store_true',
            dest='no_folder_per_app',
            default=False,
            help='Disable creation of folders for each migrated app and put all migrations into same folder',
        )

    def handle(self, out_folder, **options):
        loader = MigrationLoader(connection=connections[DEFAULT_DB_ALIAS])
        # Prevent override apps folders
        if out_folder == '.':
            out_folder = self.out_folder_default

        # Call sqlmigrate for all migrations of each app
        bar = progressbar.ProgressBar()
        migrations = self.get_all_migrations(loader)
        for i in bar(range(len(migrations))):
            migration = migrations[i]
            self.write_sqlmigrate(out_folder, migration, options['no_folder_per_app'])

        self.stdout.write(self.style.SUCCESS(self.command_sucessfull_finish %(os.path.abspath(out_folder))))

    def get_all_migrations(self, loader):
        migrations = []
        graph = loader.graph
        for app_label in loader.migrated_apps:
            for node in graph.leaf_nodes(app_label):
                for plan_node in graph.forwards_plan(node):
                    if plan_node not in migrations and plan_node[0] == app_label:
                        migrations.append(plan_node)
        return migrations

    def write_sqlmigrate(self, out_folder, migration, no_apps_folder=False):
        app_label = migration[0]
        migration_name = migration[1]
        migration_prefix = migration[1].split('_')[0]
        filename = migration_name + '.sql' 
        directory = out_folder

        if not no_apps_folder:
            directory = os.path.join(os.path.normpath(out_folder), app_label)
        else:
            filename = app_label + '_' + filename

        self.create_directory(directory)
        file_path = os.path.join(directory, filename)
        with open(file_path, 'w+') as sql_file:
            call_command('sqlmigrate', app_label, migration_prefix, stdout=sql_file)
        
    def create_directory(self, path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise