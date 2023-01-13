#This Script creates the dev environment, it assumes that python is already installed

#Script Variables
$folder = "env"
$env_name = "fitbit-dev"
#create the env folder if it doesnt already exist
set-location ..
If(!(test-path -PathType container $folder))
{
    New-Item -ItemType Directory -Path $folder
}
set-location $folder
#Create the virtual env if the folder doesnt exist
If(!(test-path -PathType container $env_name))
{
    python -m venv $env_name
}

#TODO Add installing requirements.txt file