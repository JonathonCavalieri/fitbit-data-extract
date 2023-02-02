import os
import shutil

# FUNCTION_NAME = "FitbitExtract"
# SOURCE_DIR = os.path.join("Source", FUNCTION_NAME)
# DESTINATION_DIR = "packaged_zips"


def package_cloud_function(
    function_name,
    source_dir="Source/FitbitExtract",
    destination_dir="packaged_zips",
    config_file="config.json",
) -> None:
    def check_prefix(file_name: str) -> bool:
        exclude_prefixes = ["__", "test", "local"]

        check = [file_name.startswith(prefix) for prefix in exclude_prefixes]

        return not any(check)

    # Clear and recreate temp directory
    temp_dir = os.path.join(destination_dir, "temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)

    # Copy Config to temp directory
    if os.path.exists(config_file):
        config_destination = os.path.join(temp_dir, config_file)
        shutil.copyfile(config_file, config_destination)

    # Get all files. remove temp, local and testings files
    files = os.listdir(source_dir)
    files = [file for file in files if check_prefix(file)]

    # Copy files and folders to temp location
    for file in files:
        source = os.path.join(source_dir, file)
        destination = os.path.join(temp_dir, file)
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copyfile(source, destination)

    # Make an archive of the file
    archive_name = os.path.join(destination_dir, function_name)
    if os.path.exists(archive_name):
        os.remove(archive_name)
    shutil.make_archive(archive_name, "zip", temp_dir)
    shutil.rmtree(temp_dir)


def main() -> None:
    package_cloud_function("Fitbit")
    # package_cloud_function("FitbitLoad")


if __name__ == "__main__":
    main()
