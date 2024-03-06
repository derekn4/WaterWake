<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <!--<a href="https://github.com/derekn4/CurfewBot?tab=readme-ov-file">
    <img src="curfew.png" alt="Logo" width="300" height="300">
  </a>-->

<h3 align="center">Water Wake</h3>

  <p align="center">
    Utilizing Computer Vision for head detection, activated by an alarm clock, to shoot water at my face.
    <br />
    <a href="https://github.com/derekn4/WakerWake"><strong>Explore the docs »</strong></a>
    <br />
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
        <li><a href="#libaries-used">Libraries Used</a></li>
      </ul>
    </li>
    <li>
      <a href="#head-detection">Head Detection</a>
    </li>
    <li>
      <a href="#alarm">Alarm</a>
    </li>
    <li>
      <a href="#shooting-water">Shooting Water</a>
    </li>
    <li>
      <a href="#roadmap">Roadmap</a>
    </li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project
Have you ever struggled to wake up in the morning? Are regular alarm clocks not enough (even when you set multiple alarms)?
Did you develop muscle memory to snooze or even turn off your alarm?

This project idea came from my struggle to wake up in the morning. At one point I thought, "I wish someone would just punch me awake."
And then, I remembered splashing water in my face to wake up and thought, "Hey...what if I could do both?"
Overall, I wanted to continue working with ML and decided that this project would be a fun development.

WaterWake (..or SquirtAlarm) is meant as a fun project to utilize Computer Vision and learn some mechanical engineer create a fool-proof alarm.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built With

* [![Python][Python.org]][Python-url]
* <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/OpenCV_Logo_with_text_svg_version.svg/1200px-OpenCV_Logo_with_text_svg_version.svg.png" alt="OpenCV" width="100"/>
* RaspberryPi
* Arduino
* Swift (potentially)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Libraries Used
* opencv-python
* dlib
* numpy

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Head Detection
Initially, I thought that a simple facial detection would suffice for this portion, but then, I realized that I sleep on my side and a standard face detection code would not suffice.
- I actually did try various version before landing on my head_detection code, including CV2's facial detection

- the head_detection.py code utilizes the CV2 and the dlib library
  - with the get_frontal_face_detector() from the dlib library, I could get the original face detection
  - I added the lock-on code for the bounding box to continue tracking my head, despite the change in angle
- Additionally, there is a head-pose-estimation code that can detect ears
  - with this code, when the camera turns on, it will look for either my **entire face** or **one of my ears** and use those to track my head

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Alarm
- Work in Progress
- Plan: iOS application to set alarm and send trigger to my laptop to activate the head detection

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Shooting Water
- Work in Progress
- Plan: Arduino and RaspberryPi connected to my laptop and used to:
  - Aim the watergun 
  - Shoot water

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

- [X] Head Detection
  - [X] Camera can detect head
  - [X] Side profile detection
  - [X] Head detection draws bounding box and locks on
  - [X] Bounding box remains locked when side profile
  - [X] Triggers a stop if head not detected for more than 10 seconds
- [ ] Alarm Function
  - [ ] Sends trigger to a server when alarm goes off
  - [ ] Trigger activates Head detection code
- [ ] Watergun Mechanism
  - [ ] Obtains head detection input
  - [ ] Aims watergun
  - [ ] Shoot water accurately at head

See the [open issues](https://github.com/derekn4/WakerWake/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

Derek Nguyen 
- [LinkedIn](https://www.linkedin.com/in/derekhuynguyen/) 
- [Email](derek.nguyen99@gmail.com)
<br></br>
Project Link: [https://github.com/derekn4/WakerWake](https://github.com/derekn4/WakerWake)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[Python.org]: https://www.python.org/static/img/python-logo.png
[Python-url]: https://www.python.org/about/website/
[opencv.org]: https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/OpenCV_Logo_with_text_svg_version.svg/1200px-OpenCV_Logo_with_text_svg_version.svg.png
[opencv-url]: https://opencv.org/