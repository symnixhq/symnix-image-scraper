"""
A script that fetches Docker image tags, updates a local JSON file, 
and optionally syncs with an API, including deleting outdated tags.
"""

import json
import os
import re
import requests
import concurrent.futures
import argparse

API_URL = "https://api.example.com"  # Replace with the actual API URL
API_TOKEN = os.getenv("X_API_TOKEN")  # Token should be set as an environment variable

def get_docker_image_tags(image):
    """
    Fetches and filters Docker image tags from Docker Hub.

    Args:
        image (str): The name of the Docker image.

    Returns:
        list: List of the latest 5 unique version tags sorted in descending order.
    """
    tags = []

    if "/" in image:
        username, repo_name = image.split("/")
        tags.extend(get_docker_image_tags_specific_repo(username, repo_name))
    else:
        tags.extend(get_docker_image_tags_official_repo(image))

    version_tags = [tag for tag in tags if re.match(r'v?\d+(\.\d+){0,2}', tag)]
    versions = [{'version': re.match(r'v?(\d+(\.\d+){0,2})', tag).group(1), 'major': re.match(r'v?(\d+)', tag).group(1)} for tag in version_tags]
    unique_versions = []
    seen_versions = set()

    for version in sorted(versions, key=lambda v: tuple(map(int, v['version'].split('.'))), reverse=True):
        if version['version'] not in seen_versions:
            seen_versions.add(version['version'])
            unique_versions.append(version)

    return unique_versions[:10]


def get_docker_image_tags_official_repo(image):
    url = f"https://registry.hub.docker.com/v2/repositories/library/{image}/tags?page_size=1000"
    return _fetch_and_parse_tags(url)


def get_docker_image_tags_specific_repo(username, repo_name):
    url = f"https://registry.hub.docker.com/v2/repositories/{username}/{repo_name}/tags?page_size=1000"
    return _fetch_and_parse_tags(url)


def _fetch_and_parse_tags(url):
    tags = []
    while url:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        data = response.json()
        tags.extend([result["name"] for result in data["results"]])
        url = data.get("next")
    return tags

def fetch_all_container_images():
    """
    Fetches all container images from the API.

    Returns:
        list: A list of all images with their IDs and names.
    """
    response = requests.get(f"{API_URL}/container-images", headers={"X-API-TOKEN": API_TOKEN})
    response.raise_for_status()
    return response.json()

def fetch_image_versions(image_name):
    """
    Fetches all versions of a container image from the API.

    Args:
        image_name (str): Name of the container image.

    Returns:
        list: A list of version strings for the specified image.
    """
    response = requests.get(f"{API_URL}/container-image-versions/{image_name}", headers={"X-API-TOKEN": API_TOKEN})
    response.raise_for_status()
    return response.json()

def send_to_api(updated_tags):
    """
    Sends updated tags to the API.

    Args:
        updated_tags (dict): Dictionary of updated image tags to send to the API.
    """
    payload = {
        "images": [
            {"name": image, "versions": tags} for image, tags in updated_tags.items()
        ]
    }
    response = requests.post(f"{API_URL}/container-images", json=payload, headers={"X-API-TOKEN": API_TOKEN})
    response.raise_for_status()

def delete_container_image(image_id):
    """
    Deletes a container image by ID from the API.

    Args:
        image_id (str): ID of the container image to delete.
    """
    response = requests.delete(f"{API_URL}/container-images/{image_id}", headers={"X-API-TOKEN": API_TOKEN})
    response.raise_for_status()

def compare_and_identify_deletions(image_name, latest_tags, api_tags):
    """
    Compares the latest tags with the API tags to identify outdated versions.

    Args:
        image_name (str): The name of the Docker image.
        latest_tags (list): List of the latest tags fetched from Docker Hub.
        api_tags (list): List of tags currently stored in the API.

    Returns:
        list: Tags from the API that are not in the latest tags (outdated tags).
    """
    latest_versions = [tag['version'] for tag in latest_tags]
    outdated_versions = [tag for tag in api_tags if tag not in latest_versions]
    return outdated_versions


def main(enable_api=False):
    """
    Main function to manage Docker image tags and optionally sync with an API.
    """
    with open('services.json', 'r', encoding='utf-8') as f:
        services = json.load(f)

    updated_tags = {}
    if not os.path.exists('all_tags.json'):
        with open('all_tags.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)

    with open('all_tags.json', 'r', encoding='utf-8') as f:
        all_tags = json.load(f)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(get_docker_image_tags, service['name']): service['name'] for service in services}

        for future in concurrent.futures.as_completed(futures):
            image = futures[future]
            try:
                new_tags = future.result()
            except Exception as e:
                print(f'Error fetching tags for {image}: {e}')
                continue

            current_tags = all_tags.get(image, [])
            current_versions = [tag['version'] for tag in current_tags]
            newer_tags = [tag for tag in new_tags if tag['version'] not in current_versions]
            if newer_tags:
                updated_tags[image] = newer_tags + current_tags

    if updated_tags:
        all_tags.update(updated_tags)
        with open('all_tags.json', 'w', encoding='utf-8') as f:
            json.dump(all_tags, f, indent=4)

        if enable_api and API_TOKEN:
            send_to_api(updated_tags)

            for image_name in updated_tags.keys():
                api_tags = fetch_image_versions(image_name)
                outdated_tags = compare_and_identify_deletions(image_name, updated_tags[image_name], api_tags)
                for outdated_version in outdated_tags:
                    print(f"Deleting outdated version '{outdated_version}' for image '{image_name}'")
                    delete_container_image(outdated_version)

        print('Updated tags written to all_tags.json')
    else:
        print('No newer tags found. all_tags.json remains unchanged.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Docker image tags and optionally sync with an API.")
    parser.add_argument('--enable-api', action='store_true', help="Enable API integration.")
    args = parser.parse_args()

    main(enable_api=args.enable_api)
