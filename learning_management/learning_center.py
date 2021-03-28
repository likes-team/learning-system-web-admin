from app.core import CoreModule
from .models import Teacher, Student, TrainingCenter



class LearningManagementModule(CoreModule):
    module_name = 'learning_management'
    module_icon = 'fa-map'
    module_link = 'lms.training_centers'
    module_short_description = "Learning Management"
    module_long_description = "Learning Management System"
    models = [
        TrainingCenter, Teacher, Student
    ]
    version = '1.0'
    sidebar = {
        'Training Centers': [TrainingCenter],
        'System': [Teacher, Student]
    }
