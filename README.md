<a id="readme-top"></a>
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Unlicense License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Gemeto/SpainHouses/">
  </a>

  <h3 align="center">SpainHouses</h3>

  <p align="center">
    Crawler, analyzer and visualizer for real state offers in Spain.
    <br />
    <a href="https://github.com/Gemeto/SpainHouses/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/Gemeto/SpainHouses/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This project is a base automation for common tasks of extracting, analyzing and visualizing real estate offers data.

The tool is formed by three main modules:
1. Crawler:
   * Crawler for real estate platforms, offers filtering options to the user for efficiency reasons and it's compatible with Selenium for dynamic content load
2. Web
   * Real estate like web with custom metrics like prices histiorics statistics or image based suggestions among all the crawled offers
3. Image feature extraction
   * Image feature extraction using ResNet50 for all the images crawled

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

Languages:
* Python

Frameworks:
* Flusk
* Scrapy

Libraries:
* Tensorflow
* scikit-learn
* seleniumbase
* pymongo
* dateparser
* pillow

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

Here you can find the prerequisites needed and the installation and usage guides

### Prerequisites

To launch this tools you'll need to install:
* Google Chrome
* Python 3.12
* Docker desktop
* Cuda>=12.3 (Only to run the image comparator without Docker)

### Installation

1. Install prerequisites on the local machine
2. Clone the repo
	```sh
	git clone https://github.com/Gemeto/SpainHouses
	```
3. Create a file named '.env' inside the root folder and set the following required fields:
	```sh
	MONGO_DB = "your_db_name"
	MONGO_USER = "your_username"
	MONGO_PASS = "your_pass"
	MONGO_HOST = "your_hostname"
  GEOCODIFY_API_KEY = "your_geocodify_api_key"
	```
4. Create a venv inside './crawler', activate it and install requirements (Recommended)
	```sh
	cd ./crawler
	python -m venv env
	env/scripts/activate
	pip install -r requirements.txt
	```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

* Launch modules with docker compose
	* Launch only the db service
	```sh
	docker compose --profile db up
	```
	* Launch the web module with db service
	```sh
	docker compose --profile web up
	```
	* Launch the image feature extractor module with db service
	```sh
	docker compose --profile comparator up
	```
* Execute the crawler module (docker compose db service is REQUIRED)
	```sh
 	cd./crawler
	python ./main.py (use --help to see available params)
	```
<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Top contributors:

<a href="https://github.com/Gemeto/SpainHouses/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Gemeto/SpainHouses" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the Unlicense License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/Gemeto/SpainHouses/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Gemeto/SpainHouses.svg?style=for-the-badge
[forks-url]: https://github.com/Gemeto/SpainHouses/network/members
[stars-shield]: https://img.shields.io/github/stars/Gemeto/SpainHouses.svg?style=for-the-badge
[stars-url]: https://github.com/Gemeto/SpainHouses/stargazers
[issues-shield]: https://img.shields.io/github/issues/Gemeto/SpainHouses.svg?style=for-the-badge
[issues-url]: https://github.com/Gemeto/SpainHouses/issues
[license-shield]: https://img.shields.io/github/license/Gemeto/SpainHouses.svg?style=for-the-badge
[license-url]: https://github.com/Gemeto/SpainHouses/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/daniel-mart%C3%ADnez-valeriano-0b77b5167/
