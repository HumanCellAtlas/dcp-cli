# SOP for pilot submitters providing data files to the HCA Data Coordination Platform

This SOP describes how to submit data files to the HCA Data Coordination Platform (DCP) for the DCP pilot software release. Currently, the `hca` command line tool (hca-cli) is used to transfer data files to Amazon S3.

## Requirements

- A system running Unix (Linux or MacOS).
- The system's clock must be within 15 minutes of accurate. We suggest using [ntpdate](http://doc.ntp.org/4.1.1/ntpdate.htm) or [date](https://www.tutorialspoint.com/unix_commands/date.htm) to fix this if your system does not have NTP setup.
- Python 2.7, 3.4, 3.5, or 3.6 with `pip` installed. Instructions for how to install `pip` can be found [here](https://pip.pypa.io/en/stable/installing/).

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

1. Navigate to the data files, replacing `</path/to/data>` with the path to where the data files are:

    ```
    cd </path/to/data>
    ```

1. Upload the data files to the upload area, replacing `<data-files>` with the data filenames:

    ```
    hca upload file <data-files>
    ```

The hca-cli supports [wildcards](https://en.wikibooks.org/wiki/A_Quick_Introduction_to_Unix/Wildcards) which allows multiple files to be uploaded using one command if they have a common naming convention. For example,

```
hca upload file *.fastq.gz
```

will upload all files in the current directory where the filename ends in `.fastq.gz`.

A list of files present in the selected upload area can be viewed by running:

```
hca upload list -l
```

## Note

* Files cannot be deleted from the upload area using the `hca` tool. If there are files that need to be deleted, please contact data-help@humancellatlas.org and include your name, credentials, and a list of filenames to delete.
* Uploading a file with the same filename as one that already exists in the upload area will replace the file with the most recent upload. You can find out what files are already in the system using the command hca upload list -l
* For more information about the hca-cli, you can check out documentation on
[GitHub](https://github.com/HumanCellAtlas/dcp-cli) or [readthedocs](http://hca.readthedocs.io/en/latest/).
