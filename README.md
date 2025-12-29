# ogfimg
OGF/OSM Image/tile downloader and stitcher

This is a simple tool I made with ChatGPT for downloading tiles on [OGF](https://opengeofiction.net), OSM or Arhet then stitching them to one pretty map.
![banner](/images/ex1.png)
## Setup

First install the following dependencies with:
`pip install flask requests pillow`

After that you should be able to just run the app.py then on port 5000 of the machine you put it on it should show the site ready to use.

 ## Usage
Its really quite simple where you either enter your zoom, start lat and lon, and end lat and lon, or just use the box tool and enter your zoom level. After that seclect "Start Download" where a progress bar will show how many tiles it has downloaded, once complete select "Stitch Map" and after some time it will let you download your image. If you happen to refresh the page before download you canfind it under /download/map_X.png (replace X with its real number).
 
Sometimes the download never completes because some tiles are mising and if that happens just click stitch map and once you download the map refresh the main page.

### Once Done
Once you are done with downloading an image always refresh the main page (just in case there are errors)

If you are done with making images it can stay on or you can just stop it by closing the command prompt.

## Examples

![Oban, Scotland in openbusmap](/images/ex2.png)
*Oban, Scotland (OPNVKARTE)*

![Roantra, West Uletha in OGF carto](/images/ex3.png)
*Roantra, West Uletha in OGF carto*

![KFC sponsored dicatatorship in Arhet-Carto](images/ex4.png)
*KFC sponsored dicatatorship in Arhet-Carto*

![Linlithgow, Humanitarian](/images/ex5.png)
*Linlithgow in Humanitarian style*

![Belfast city centre, OSM France](/images/ex6.png)
*Belfast city centre in OSM France style*
