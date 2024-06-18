[![CI](https://github.com/ekalinin/github-markdown-toc/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/ekalinin/github-markdown-toc/actions/workflows/ci.yml)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/ekalinin/github-markdown-toc)


<a name="readme-top"></a>
<div id="header" align="center">

  <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/80728820-e06b-4f96-9c9e-9df46f0cc0a5" width="600">
<br><br>
</div>

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
  - [Dataset Synthesis](#dataset-synthesis)
  - [Machine-Learning](#machine-learning)
  - [Miscellaneous Deprecated](#miscellaneous-deprecated)
  - [Requirements txt Note](#requirements-txt-note)
    
<!--te-->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

### Mission Statement 

>  The mission of CEES is to facilitate education, research, and outreach in the earth and environmental studies across the TAMIU service area. CEES also takes pride in supporting diverse research endeavors across the TAMIU campus. This beginner-friendly guide aims to simplify the understanding of raster, files, and other related concepts by utilizing the OS library and ArcPy package in the operating environment.

:arrow_right: *[https://www.tamiu.edu/cees/](https://www.tamiu.edu/cees/)*


<div id="header" align="center">
  <img src="https://github.com/TAMIUCEES/ML-DownScale_SMERGE_CEES/assets/166143344/30e6a11e-0451-4d2d-bc8f-9acb53494091.image.svg" title="ceeslogo" alt="ceeslogo"  align ="center" width="140" height="140"/>&nbsp;
</div>




## Explanation of Structure 

> * The user can start with the first file folder, **ArcPy_Scripts**.
> *  There are four distinct folders in total. After the **ArcPy_Scripts** folder, users will proceed to the **Dataset_Synthesis** folder, followed by the **Machine_Learning** folder, and lastly, the **Miscellaneous_Deprecated** folder.
> *   Each folder consists of subfolders that contain notebooks and scripts equipped with a range of tools. These tools are designed to assist in organizing and presenting pertinent data efficiently, enabling users to access and manipulate information more effectively. This enhanced productivity and predictive capabilities contribute to improved overall performance and accuracy.

---
---

###   Acrpy Scripts 

> * **Included Notebooks and Python Scripts:**
>     * MDR_layer_extractor_v1
>     * auto_multiD_subsetting
>     * auto_zonal_stats
>     * multiBand_raster_extractor
>     * multiD_raster_merge
>     * netCDF_layer_extractor
>     * raster_merge

> * Libraries used:
>     *  This guide will provide a comprehensive explanation of the directory structure and offer a step-by-step guide to utilizing the **os** library and **ArcPy** packages. The programs will consistently employ the libraries to ensure cohesion.

>  [!NOTE]
> * To initiate the process, the *auto_multiD_subsetting* program should be utilized first. Subsequently, based on the user's requirements, any intermediate programs can be employed as needed. It is essential to finalize the process with the *auto_zonal_stats* program as the final step.
---

> * *auto_multiD_subsetting*:
>      *  The program facilitates efficient data retrieval and raster processing by subsetting and resampling raster data on an individual layer basis.

> * *multiD_raster_merge*:
>      *  This program is designed to combine multiple multidimensional raster datasets into a single, cohesive raster dataset.

> * *multiBand_raster_extractor*: 
>      *  The program is equipped with efficient band extraction and reordering capabilities, enabling the extraction of one or more bands or reorganizing the bands into a multiband raster layer effectively.     
                
> * *netCDF_layer_extractor*:
>      *  This program utilizes the **find_files** function to identify files and construct new file paths, allowing users to generate new files and perform data resampling.

> * *raster_merge*:
>      *   This program enables users to merge multiple raster files, consolidating diverse datasets into a single comprehensive raster.

> * *auto_zonal_stats*:
>      *  This program allows users to resample files, enabling raster file size conversion. 

> Additional:
> *  *MDR_layer_extractor_v1*:
>       *  Through data slicing along specific variables and dimensions, the program extracts subsets from numerous multidimensional raster datasets, enabling the generation of a multidimensional raster layer from a given dataset.

--- 
---
### Dataset Synthesis 

> * **Included Notebooks and Python Scripts:**
>     * dataset_breakdown
>     * inst_post_process
>     * primary_dataset_gen
>     * static_var_gen

 > * These notebooks are designed to arrange and display pertinent data methodically. By doing so, users can access and manage the required information. 

 > [!NOTE]
>  * In the notebook sequence, the *dataset_breakdown* and *static_var_gen* notebooks can be used interchangeably and should come before all other notebooks. After these two notebooks, the *primary_dataset* notebook can be used. Finally, the *inst_post_process* notebook is optional, but if used, it should be placed at the end of the sequence.


--- 

> * *dataset_breakdown*:
>    *  The program gathers data from the user input in the form of a CSV file or files then breaks down the data in the file.

> * *static_var_gen*:
>    *  The program generates a new CSV file using static variables from the initial dataset.

> * *primary_dataset_gen*:
>    *  The program enhances prediction accuracy by generating, cleaning, and combining data from static and dynamic files.

> * *inst_post_process*:
>    *  The program organizes data from two files to obtain updated station names and pagenames.

---
---
## Machine-Learning

> * **Included Notebooks and Python Scripts:**
>     *  GBR_w_verifer
>     *  GBR_wout_verifier
>     *  RF
>     *  XGB_w_verifier
>     *  XGB_wout_verifier

> * These notebooks aim to provide users with a reference to machine-learning techniques, specifically guiding them through the process of constructing and utilizing multiple decision trees. The ultimate objective is to enhance the accuracy and overall predictive capabilities of the constructed models.

---

> * *GBR_w_verifer*: 
>    *   The Gradient Boosting Regressor with verifier is a machine learning algorithm that employs a sequence of decision trees to perform predictions.

> * GBR_wout_verifier: 
>    *   This machine-learning technique will be used without a verifier. This machine-learning algorithm uses a series of decision trees to make predictions, each prediction is trained to correct the errors of previous trees which results in an accurate overall prediction.

> * RF:
>    *   The machine learning technique Random forest (RF) is a machine learning algorithm that generates a single prediction by collecting the output of multiple decision trees. 
>        * Disclaimer: Random Forest(RF ) ONLY runs with Linux.

> * XGB_w_verifier:  
>    *   This machine learning algorithm uses eXtreme Gradient Boost (XGBoost) with a verifier. This machine learning algorithm builds a series of trees one after another while excelling in predictive accuracy. 

> * XGB_wout_verifier:
>   *  This machine learning technique uses eXtreme Gradients boost (XGBoost) without a verifier.
>   *   Like the XGB_w_verifier, this machine learning algorithm builds a series of trees one after another while excelling in predictive accuracy.

---
***
### Miscellaneous Deprecated 

> * Notebooks and py_scripts included:  aggregate_multipoints, MDR_layer_extractorV2, and auto_multipoint_extractor.
> * **Note:** Miscellaneous ArcPy notebooks that are not being used but can be helpful to the user.

---

> * Aggregate_Multipoints:
>   *  The Aggregate_multipoints script summarizes point features, allowing these points to create an area and are used to calculate statistics. 

> * MDR_Layer_ExtractorV2:
>   *  The MDR_layer_extractorV2 program utilizes the function to extract subsets from multiple multidimensional raster datasets by saving the datasets to a designated directory.


> * Auto_Multipoint_Extractor:
>    *  Auto_multipoint_extractor program allows users to extract multiple points automatically by modifying the input point features. 



---
---

###  Requirements txt Note

ghggjjgjgjjgjjg




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


