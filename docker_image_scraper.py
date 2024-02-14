"""
A script that takes a list from a file called 'services.json'
and returns the latest 10 image tags that are human readable
in a sorted view (from newest to oldest image) in a file called 'all_tags.json'
"""

import json
import os
import re
import concurrent.futures
import requests

def get_docker_image_tags(image):
    """
    Fetches and filters Docker image tags from Docker Hub.

    Args:
        image (str): The name of the Docker image.

    Returns:
        list: List of the latest 10 unique version tags sorted in descending order.
    """
    tags = []

    if "/" in image:
        username, repo_name = image.split("/")
        tags.extend(get_docker_image_tags_specific_repo(username, repo_name))
    else:
        if image.startswith("https://hub.docker.com/r/"):
            image_parts = image.split("/")
            repo_name = image_parts[-2]
            image_name = image_parts[-1]
            tags.extend(get_docker_image_tags_specific_repo(repo_name, image_name))
        else:
            tags.extend(get_docker_image_tags_official_repo(image))

    tags = list(set(tags))

    # Filter out tags that don't seem to follow a versioning scheme
    version_tags = [tag for tag in tags if re.match(r'v?\d+(\.\d+){0,2}', tag)]

    # Extract version from each tag
    versions = [re.match(r'v?(\d+(\.\d+){0,2})', tag).group(1) for tag in version_tags]

    # Get only unique versions, preserving order
    unique_versions = list(dict.fromkeys(versions))

    # Sort versions in descending order
    unique_versions = sorted(unique_versions, key=lambda v: tuple(map(int, v.split('.'))), reverse=True)

    return unique_versions[:10]


def get_docker_image_tags_official_repo(image):
    """
    Fetches tags for an image in the official Docker Hub repository.

    Args:
        image (str): The name of the Docker image.

    Returns:
        list: List of tags for the image.
    """
    url = f"https://registry.hub.docker.com/v2/repositories/library/{image}/tags?page_size=1000"
    return _fetch_and_parse_tags(url)


def get_docker_image_tags_specific_repo(username, repo_name):
    """
    Fetches tags for an image in a user's Docker Hub repository.

    Args:
        username (str): The username of the Docker Hub account.
        repo_name (str): The name of the Docker repository.

    Returns:
        list: List of tags for the image.
    """
    url = f"https://registry.hub.docker.com/v2/repositories/{username}/{repo_name}/tags?page_size=1000"
    return _fetch_and_parse_tags(url)


def _fetch_and_parse_tags(url):
    """
    Fetches tags from a URL and parses the JSON response.

    Args:
        url (str): URL to fetch the tags from.

    Returns:
        list: List of tags fetched from the URL.
    """
    tags = []
    while url is not None:
        response = requests.get(url, timeout=300)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        data = response.json()
        tags.extend([result["name"] for result in data["results"]])
        url = data.get("next")
    return tags

def main():
    """
    Main function to read services from a JSON file, fetch their latest tags,
    and write the updated tags to a JSON file.
    """
    with open('services.json', 'r', encoding='utf-8') as f:
        services = json.load(f)

    updated_tags = {}

    if not os.path.exists('all_tags.json'):
        with open('all_tags.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)

    with open('all_tags.json', 'r', encoding='utf-8') as f:
        all_tags = json.load(f)

    # Create a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start fetching tags for each image in a separate thread
        futures = {executor.submit(get_docker_image_tags, service['name']): service['name'] for service in services}

        # As each future completes, update the tags
        for future in concurrent.futures.as_completed(futures):
            image = futures[future]
            try:
                new_tags = future.result()
            except Exception as e:
                print(f'Error fetching tags for {image}: {e}')
                continue

            current_tags = all_tags.get(image, [])
            newer_tags = [tag for tag in new_tags if tag not in current_tags]
            if newer_tags:
                updated_tags[image] = newer_tags + current_tags

    if updated_tags:
        all_tags.update(updated_tags)
        with open('all_tags.json', 'w', encoding='utf-8') as f:
            json.dump(all_tags, f, indent=4)

        print('Updated tags for', list(updated_tags.keys()), 'written to all_tags.json')
    else:
        print('No newer tags found. all_tags.json remains unchanged.')


if __name__ == "__main__":
    main()
