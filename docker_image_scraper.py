import requests
import json

def get_docker_image_tags(image, include_user_repos=True):
    """Retrieves and sorts Docker image tags from the Docker Hub registry.

    Args:
        image (str): The name of the Docker image to query.
        include_user_repos (bool, optional): Whether to include user public repositories. Defaults to False.

    Returns:
        list: A list of sorted image tags (including specific repo if provided).
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

    # Remove duplicates and sort
    tags = list(set(tags))
    tags.sort(key=str.lower)  # Case-insensitive sorting

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

if __name__ == "__main__":
    import sys

    # Handle specific URL input if provided
    if len(sys.argv) > 1 and sys.argv[1].startswith("https://hub.docker.com/r/"):
        image = sys.argv[1]  # Extract image name and repository from URL
        tags = get_docker_image_tags(image)
    else:
        image = sys.argv[1] if len(sys.argv) > 1 else ""
        tags = get_docker_image_tags(image)

    print("\n".join(tags))
