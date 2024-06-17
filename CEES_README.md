[![CI](https://github.com/ekalinin/github-markdown-toc/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/ekalinin/github-markdown-toc/actions/workflows/ci.yml)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/ekalinin/github-markdown-toc)


<a name="readme-top"></a>
<div id="header" align="center">

  <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/80728820-e06b-4f96-9c9e-9df46f0cc0a5" width="600">
<br><br>
</div>





<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#mission-statement">Mission Statement</a>
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
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#acrpy-scripts">Acrpy Scripts</a></li>
    <li><a href="#dataset-syntesis">Dataset syntesis</a></li>
    <li><a href="#machine-learning">Machine-Learning</a>
    <li><a href="#miscellaneous-deprecated">Miscellaneous Deprecated</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!--
To update TOC, please run:
> doctoc ./README.md --github
 -->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!--ts-->
---   
  ## Table of Contents 
  - [Mission Statement](#mission-statement)
    - [Explanation of Structure](#explanation-of-structure)
  - [Acrpy Scripts](#acrpy-scripts)
  - [Dataset Syntesis](#dataset-syntesis)
  - [Machine-Learning](#machine-learning)
  - [Miscellaneous Deprecated](#miscellaneous-deprecated)
    
<!--te-->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

### Mission Statement 

>  The mission of CEES is to facilitate education, research, and outreach in the earth and environmental studies across the TAMIU service area. CEES also takes pride in supporting diverse research endeavors across the TAMIU campus. This brief guide outlines the OS library and the ArcPy package employed in the environment used. The goal is to make interpreting raster, files, etc, as beginner-friendly as possible. 


<div id="header" align="center">
  <img src="https://github.com/TAMIUCEES/ML-DownScale_SMERGE_CEES/assets/166143344/30e6a11e-0451-4d2d-bc8f-9acb53494091.image.svg" title="ceeslogo" alt="ceeslogo"  align ="center" width="128" height="128"/>&nbsp;
</div>



## Explanation of structure 
> By entering the main branch in Github, the user will have access to the files. The user can start with the file folder. 
The CEES  database repository is a tool for Python and ArcGIS. This tool can help the user re-sample raster images.
Steps: → arcpy → dataset → machine_learning→ Miscellaneous deprecated 

---


###   Acrpy Scripts 

* Notebooks and Py_scipts included: auto_multiD_subsetting, multiD_rasters_merge, MultiBand_Raster_Extractor,  netCDF_Layer_extractor,  raster_merge, auto_zonal_stats,and zonal_statistics.
  *   Below are the contents listed in the user's recommended order. 

* Libraries used:
     *  The programs will use the OS library and ArcPy package consistently. This guide will explain the structure of the directories and serve as a step-by-step guide to using the libraries. 
 
* Auto_multiD_subsetting:
   *  Similar to the auto_zonal_stats program, it facilitates efficient data retrieval and processing by subsetting and resampling raster data layer-by-layer.

*  multiD_rasters_merge:
      *  This program is designed to combine multiple multidimensional raster datasets into a single, cohesive raster dataset.

*  The MultiBand_Raster_Extractor: 
        *  This program, utilizing user inputs, generates a new file containing the band numbers that comprise a raster.                                             
                  
* The netCDF_Layer_extractor:
       *  This program leverages the find_files function to identify files and construct new file paths, allowing users to modify file names for each path.

*  The raster_merge:
      *   This program enables users to merge multiple raster files, consolidating diverse datasets into a single comprehensive raster.

*  The auto_zonal_stats:
   *  This program allows users to resample files, enabling raster file size conversion. 

*  The Zonal Statistics:
       *  This program calculates statistics on raster values within zones of another dataset.

--- 

### Dataset Syntesis 

 > * Notebooks and Py_scipts: include the dataset_breakdown, inst_post_process, primary_dataset_gen, static_var_gen. 
 > * These notebooks serve a specific purpose by organizing and presenting relevant data sequentially, enabling readers to easily access and manipulate the necessary information.

> *  The notebook order should be as follows: dataset_breakdown, static_var_gen (interchangeable), and primary_dataset_genV2. Lastly, the inst_post_process is optional. 

> *   Note: 
Pandas are extensively used throughout the notebooks. 

--- 

* Dataset_breakdown:
    *  The program allows users to break down a CSV file or files based on input. 

* Static _var_gen:
  *  The program generated a new CSV file using static variables from the initial dataset.

* Primary_dataset_gen:
   *  The program enhances prediction accuracy by generating, cleaning, and combining data from static and dynamic files.

* Inst_post_process:
    *  The program organizes data from two files to obtain updated station and page names.

---

## Machine-Learning

> * Notebooks and py_scripts included : GBR_w_verifer, GBR_ wout_verifier_version1., RF, XGB _w _verifier , and XGB_wout verifier.
> * The purpose of these notebooks is for the user to reference machine-learning techniques to build and use a series of decision trees for better prediction. 


* GBR_w_verifer: 
    *   This machine learning technique is a machine learning algorithm that uses a series of decision trees to make predictions. 

* GBR_ wout_verifier_version1: 
    *   This machine-learning technique will be used without the verifier. This machine-learning algorithm uses a series of decision trees to make predictions. 

* RF:
    *   The machine learning technique Random forest (RF) is a machine learning algorithm that generates a single prediction by collecting the output of multiple decision trees. 
        * Disclaimer: Random Forest(RF ) ONLY runs with Linux.

* XGB _w _verifier:  
    *   This machine learning technique uses eXtreme Gradients boost (XGBoost) with a verifier. This machine learning algorithm builds a series of trees one after another while excelling in predictive accuracy. 

* XGB_wout verifier:
   *  This machine learning technique uses eXtreme Gradients boost (XGBoost) without a verifier.
   *   Like the XGB_w_verifier, this machine learning algorithm builds a series of trees one after another while excelling in predictive accuracy.

---

### Miscellaneous Deprecated 

> * Notebooks and py_scripts included:  aggregate_multipoints , MDR_layer_extractorV2 , and auto_multipoint_extractor.
> * Note: Miscellaneous ArcPy that is not being used but can be helpful to the user.

:arrow_right: *[https://keepachangelog.com](https://keepachangelog.com)*

* Aggregate_multipoints:
   *  The Aggregate_multipoints script summarizes point features, allowing these points to create an area and are used to calculate statistics. 

* MDR_layer_extractorV2:
   *  The MDR_layer_extractorV2 program utilizes the function to extract subsets from multiple multidimensional raster datasets by saving the datasets to a designed directory.


* Auto_multipoint_extractor.
   *  Auto_multipoint_extractor program allows users to extract multiple points automatically by modifying the input point features. 



---






### :hammer_and_wrench: Languages and Tools :

  
<div>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original-wordmark.svg" title="python" alt="python" width="40" height="40"/>&nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/scikitlearn/scikitlearn-original.svg" title="scikitlearn" alt="scikitlearn" width="40" height="40"/>&nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/jupyter/jupyter-original-wordmark.svg" title="jupyter" alt="jupyter" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/java/java-original-wordmark.svg" title="Java" alt="Java" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/css3/css3-plain-wordmark.svg"  title="CSS3" alt="CSS" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/html5/html5-original.svg" title="HTML5" alt="HTML" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/javascript/javascript-original.svg" title="JavaScript" alt="JavaScript" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/mysql/mysql-original-wordmark.svg" title="MySQL"  alt="MySQL" width="40" height="40"/>&nbsp;
  <img src="https://github.com/devicons/devicon/blob/master/icons/git/git-original-wordmark.svg" title="Git" **alt="Git" width="40" height="40"/>
</div>


