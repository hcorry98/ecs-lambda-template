import sys, os
currentDir = os.path.dirname(os.path.realpath(__file__))
src = os.path.dirname(os.path.dirname(currentDir))  # get path to 'src' folder
sys.path.append(src)  # add to filepath so when code is run from main.py, imports are found properly

from awsEcs.presenters.EcsTask import EcsTask

if __name__ == '__main__':
    """Main function for starting the ECS task."""
    ecsTask = EcsTask()
    ecsTask.run()
