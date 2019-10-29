# Submitting data files to the HCA Data Coordination Platform

This document describes how to submit data files to the HCA Data Coordination Platform (DCP) using the hca command line tool (hca-cli).

## Requirements

- A system running Unix (Linux or MacOS).
- The system's clock must be within 15 minutes of accurate. We suggest using [ntpdate](http://doc.ntp.org/4.1.1/ntpdate.htm) or [date](https://www.tutorialspoint.com/unix_commands/date.htm) to fix this if your system does not have NTP setup.
- Python 3.5+ with `pip` installed. Instructions for how to install `pip` can be found [here](https://pip.pypa.io/en/stable/installing/).

## Installation

The hca-cli is used to upload files to the HCA DCP. This tool is provided by the package `hca`, which can be installed by running the following command in the terminal:

```
pip install hca
```

Once installed, more information about using the hca-cli can be found by running:

```
hca upload help
```

More details about how to install the hca-cli can be found [here](http://hca.readthedocs.io/en/latest/).

## Usage

### Credentials

The hca-cli transfers data files to a secure "upload area". Unique credentials are required to access a specific upload area. If you do not know or have these credentials, please contact us at data-help@humancellatlas.org.

### Upload files

1. Select the upload area, replacing `<credentials>` with your unique credentials:

    ```
    hca upload select <credentials>
    ```

1. Navigate to a local copy of the data files, replacing `</path/to/data>` with the path to where the data files are:

    ```
    cd </path/to/data>
    ```

1. Upload the data files to the upload area, replacing `<data-files>` with the data filenames:

    ```
    hca upload files <data-files>
    ```

The hca-cli supports [wildcards](https://en.wikibooks.org/wiki/A_Quick_Introduction_to_Unix/Wildcards) which allows multiple files to be uploaded using one command if they have a common naming convention. For example:

```
hca upload files *.fastq.gz
```

The hca-cli also supports directories as targets with an optional file extension arg. If the file extension is provided, only files matching that extension in the directory will be supported.

The following command will upload all files in the current directory where the filename ends in `.fastq.gz`:

```
hca upload files data_files_directory/ --file-extension .fastq.gz
```

A list of files present in the selected upload area can be viewed by running:

```
hca upload list -l
```

## Note

* Files cannot be deleted from the upload area using the hca-cli. If there are files that need to be deleted, please contact us at data-help@humancellatlas.org and include your name, credentials, and a list of filenames to delete.
* Uploading a file with the same filename as one that already exists in the upload area will replace the file with the most recent upload.
* For more information about the hca-cli, check out
[GitHub](https://github.com/HumanCellAtlas/dcp-cli) or [readthedocs](http://hca.readthedocs.io/en/latest/).
