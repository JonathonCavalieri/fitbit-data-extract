import os
import shutil

# FUNCTION_NAME = "FitbitExtract"
# SOURCE_DIR = os.path.join("Source", FUNCTION_NAME)
# DESTINATION_DIR = "packaged_zips"


def package_cloud_function(
    function_name, base_source_dir="Source", destination_dir="packaged_zips"
) -> None:
    def check_prefix(file_name: str) -> bool:
        exclude_prefixes = ["__", "test", "local"]

        check = [file_name.startswith(prefix) for prefix in exclude_prefixes]

        return not any(check)

    source_dir = os.path.join(base_source_dir, function_name)
    temp_dir = os.path.join(destination_dir, "temp")
    files = os.listdir(source_dir)
    files = [file for file in files if check_prefix(file)]

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    for file in files:
        source = os.path.join(source_dir, file)
        destination = os.path.join(temp_dir, file)
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copyfile(source, destination)

    archive_name = os.path.join(destination_dir, function_name)
    if os.path.exists(archive_name):
        os.remove(archive_name)
    shutil.make_archive(archive_name, "zip", temp_dir)
    shutil.rmtree(temp_dir)


def main() -> None:
    package_cloud_function("FitbitExtract")
    # package_cloud_function("FitbitLoad")


if __name__ == "__main__":
    main()
