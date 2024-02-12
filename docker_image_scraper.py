import json
import requests
import os


def get_docker_image_tags(image):
    """Retrieves and sorts latest 10 Docker image tags from the Docker Hub registry.

    Args:
        image (str): The name of the Docker image to query.
        include_user_repos (bool, optional): Whether to include user public repositories. Defaults to True.

    Returns:
        list: A list of the latest 10 sorted image tags (including specific repo if provided).
    """

    tags = []

    # Check if image includes username (e.g., "username/imagename")
    if "/" in image:
        # Extract username and search specific repository
        username, repo_name = image.split("/")
        tags.extend(get_docker_image_tags_specific_repo(username, repo_name))
    else:
        # No username provided, check if specific URL is given
        if image.startswith("https://hub.docker.com/r/"):
            # Extract image name and repository from URL
            image_parts = image.split("/")
            repo_name = image_parts[-2]
            image_name = image_parts[-1]
            tags.extend(get_docker_image_tags_specific_repo(repo_name, image_name))
        else:
            # Search official "library" repository
            tags.extend(get_docker_image_tags_official_repo(image))

    # Remove duplicates, sort descending (latest first), and keep only top 10
    tags = list(set(tags))
    tags.sort(key=str.lower, reverse=True)
    tags = tags[:10]

    return tags


def get_docker_image_tags_official_repo(image):
    """Retrieves tags for an image in the official "library" repository."""
    url = f"https://registry.hub.docker.com/v2/repositories/library/{image}/tags?page_size=1000"
    return _fetch_and_parse_tags(url)


def get_docker_image_tags_specific_repo(username, repo_name):
    """Retrieves tags for an image in a specific user repository."""
    url = f"https://registry.hub.docker.com/v2/repositories/{username}/{repo_name}/tags?page_size=1000"
    return _fetch_and_parse_tags(url)


def _fetch_and_parse_tags(url):
    """Fetches tags from a URL and parses the JSON response."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for non-200 status codes
    data = json.loads(response.text)
    tags = [result["name"] for result in data["results"]]
    return tags


def main():
    with open("services.json", "r") as f:
        services = json.load(f)

    updated_tags = {}  # Store only updated tags for modified entries

    # Check and create all_tags.json if needed
    if not os.path.exists("all_tags.json"):
        with open("all_tags.json", "w") as f:
            json.dump({}, f, indent=4)

    with open("all_tags.json", "r") as f:
        all_tags = json.load(f)

    for service in services:
        image = service["name"]
        current_tags = all_tags.get(image, [])

        # Get latest tags
        new_tags = get_docker_image_tags(image)

        # Check if any newer tags exist
        newer_tags = [tag for tag in new_tags if tag not in current_tags]
        if newer_tags:
            updated_tags[image] = newer_tags + current_tags

    # Update all_tags and write to file
    if updated_tags:
        all_tags.update(updated_tags)
        with open("all_tags.json", "w") as f:
            json.dump(all_tags, f, indent=4)

        print("Updated tags for", list(updated_tags.keys()), "written to all_tags.json")
    else:
        print("No newer tags found. all_tags.json remains unchanged.")


if __name__ == "__main__":
    main()
