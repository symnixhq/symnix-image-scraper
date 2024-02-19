<br />
<p align="center">
  This repository contains a Python3 script which we use internally as a microservice to get the latest image versions of various Docker images as a human readable version from <a href="https://hub.docker.com/"><b>Docker Hub</b></a>.
</p>
<br />

## 📃 Requirements

1. Python3 installation is required (Script is tested with version >= 3.11)
2. Run `pip install -r requirements.txt` to install the python3 requirements

<br>

## ⚡️ Usage

1. Define your images for which you need the information in the `services.json` file
   A example configuration could look like this:

   ```json
    [
	  {
	    "name": "linuxserver/bookstack"
	  },
	  {
	    "name": "nginx"
	  },
	  {
	    "name": "postgres"
	  },
	  {
	    "name": "rocketchat/rocket.chat"
	  }
    ]
   ```

2. Make sure the script has the correct permissions:

   ```bash
   chmod +x docker_image_scraper.py
   ```

3. Run the script:
   ```bash
   python3 docker_image_scraper.py
   ```

4. A successful result in the `all_tags.json` could look like this, for example:

    ```json
    {
    "nginx": [
        {
            "version": "1.25.4",
            "major": "1"
        },
        {
            "version": "1.25.3",
            "major": "1"
        },
        {
            "version": "1.25.2",
            "major": "1"
        },
        {
            "version": "1.25.1",
            "major": "1"
        },
        {
            "version": "1.25.0",
            "major": "1"
        }
    ],
    "postgres": [
        {
            "version": "16.2",
            "major": "16"
        },
        {
            "version": "16.1",
            "major": "16"
        },
        {
            "version": "16.0",
            "major": "16"
        },
        {
            "version": "16",
            "major": "16"
        },
        {
            "version": "15.6",
            "major": "15"
        }
    ],
    "linuxserver/bookstack": [
        {
            "version": "23.12.20240115",
            "major": "23"
        },
        {
            "version": "23.12.20240108",
            "major": "23"
        },
        {
            "version": "23.12.20231229",
            "major": "23"
        },
        {
            "version": "23.12.2",
            "major": "23"
        },
        {
            "version": "23.12.1",
            "major": "23"
        }
    ],
    "rocketchat/rocket.chat": [
        {
            "version": "6.6.0",
            "major": "6"
        },
        {
            "version": "6.5.3",
            "major": "6"
        },
        {
            "version": "6.5.2",
            "major": "6"
        },
        {
            "version": "6.5.1",
            "major": "6"
        },
        {
            "version": "6.5.0",
            "major": "6"
        }
      ]
    }
    ```

There are currently two attributes for each image in the `all_tags.json` output. The `version` attribute describes the respective human-readable Docker image version found and `major` indicates the major version on which the respective tag is based on.

## 🗺️ Roadmap

One of the most important features we are planning to implement is an API interface to use the output
from the microservice in your application instead of the JSON file.

We are also planning to variablize stuff like how many versions it stores for a docker image.

## 👍 Contribute

See [Contributing](CONTRIBUTING.md).

## ⚠️ License

GPLv3
