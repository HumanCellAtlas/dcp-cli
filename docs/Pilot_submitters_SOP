# SOP for pilot submitters

This SOP is for data submitters who have generated data for the pilot Data Coordination Platform software release. Follow this SOP to transfer your data files to the HCA DCP. You will be using the HCA command line interface (hca-cli) python module to transfer your data to an upload area on the Amazon cloud.


## Requirements:
A system running Unix (Linux or MacOS).
The system’s clock must be within 15 minutes of accurate (I suggest using “ntpdate” or even “date” to fix this if you system does not have NTP setup).
Python 2.7, 3.4, 3.5 or 3.6 with pip installed.

## Upload tool:
We use a command line tool called “hca” to upload files.  This is provided by the package “hca”, which you need to install running this command `$ pip install hca` int he terminal.

Use `$ hca upload help` for more information about this process at the command line.

## Credentials:
You will require unique credentials to access your upload area. If you do not already have these please contact us at data-help@humancellatlas.org

Prior to execution of the following commands please replace the placeholder `<CREDENTIALS>` with the credentials we have provided.

## Upload files

1. Select your upload area
`$ hca upload select <CREDENTIALS>`

2. Upload files
`$ cd path/to/folder/containing/your/data/files`

`$ hca upload file <your-data-files>`

* Note that the hca-cli supports [wildcards](https://en.wikibooks.org/wiki/A_Quick_Introduction_to_Unix/Wildcards). This allows you to upload multiple files in the same directory if they have a common naming convention e.g. *.fastq would upload any files where the name ends in `.fastq`

You can see which files you have uploaded to the cloud using `$ hca upload list -l`.  This will show the files in the area you have selected.

## Some other points to note
* Files cannot be deleted using the hca-cli. Contact us (data-help@humancellatlas.org) with a manifesto if there are files we should ignore. Please include your name, credentials and manifesto in this email.
* Uploading a file with the same name as one that already exists will replace the file with the most recent upload.
* For more information about the hca-cli see:
[GitHub - HumanCellAtlas/dcp-cli: HCA Data Coordination Platform Command Line Interface](https://github.com/HumanCellAtlas/dcp-cli)
