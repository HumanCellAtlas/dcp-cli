Changes for v7.0.1 (2020-02-11)
===============================

pin docutils in requirements.txt (#511)

Changes for v7.0.0 (2020-01-23)
===============================

Remove references to query service (#504) Allow user-specified bundle
uuid for upload(). (#499) Add ``httpie`` as dev requirement (#495) Fix
some progress bar tests failing silently

Changes for v6.5.1 (2019-11-26)
===============================

Move and refactor broken hardlink tests Add TestCase that creates and
uses a temp dir Set maxDiff for client tests Fix duplicate downloads
(#450) Fix parallel download test to reveal linking bug Consolidate test
code DSS Subscriptions: Callback Url (#492) Remove optional args from
super calls Work around link limit for manifest download (#427) Refactor
mocked call in test methods Rename test case Use proper configurations
for csv reading/writing (#427) Remove outdated comment Prettify the
contents of bundle.json (#444) Add API/CLI tutorial pages to Sphinx
documentation (#472) Fix dss download docstring to use correct flags
(#486) Fix documentation - remove extra periods between paragraphs
(#460) Refresh session token when the jwt expires. (#446) update version
number to revert #476 (#484) Fix import dependencies (#483) Reposition
import. (#482) Fix version numbering (#476) change flags starting with -
to start with – (#480) Fix sub-command description indentation in sphinx
docs (#479) auto pagination (#465) update required python version to
3.5+ (#459) Add Fusillade API client (#417)

Changes for v6.5.0 (2019-10-21)
===============================

-  Improvements to package dependency lists (#463)

-  Unpin cryptography dependency and set min version to 2.6.1 (#462)

-  PaginatingClientMethodFactory: Use configurable paginated content
   keys (#457)

-  Swagger client parser fixes (#451)

-  Adding header values into request when values are present in req_args
   (#447)

-  Add progress bar to ``hca dss upload`` (closes #117)

-  Deprecate python2.7 (remove python2.7 testing). (#430)

-  Modify how HCA cache is cleared (#431)

-  Fix pagination bug in download-collection

-  Add query service to documentation (#421)

-  Remove POST /search retry logic (reverts b2a87f) (#429)

-  Rename path builder to make dirs

-  Refactor download (#406)

-  Autodocs: call all SwaggerClient constructors (#416)

-  added delete for login_logout (#408)

Changes for v6.4.0 (2019-08-02)
===============================

Make filters more intuitive for manifest download (#338) Make file
filters more intuitive for bundle download (#207) Fix get collection
iteration bug. (#407) Clarify how bundle manifest can be a DSSFile
Correct bundle.json format from dict to array (#398) Fix timestamp in
bundle.json download log Rename metadata to manifest for bundle.json
download Clarity improvement to download-collection Update CLI
integration tests for brevity Skip download-collections tests on Windows
[easy] Help menu formatting. (#395) Add basic support for downloading
collections (closes #339) Download bundle metadata into bundle.json
(#231)

Changes for v6.3.0 (2019-06-17)
===============================

-  Begin DCP Query Service CLI (#359)

Changes for v6.2.0 (2019-06-12)
===============================

Read whole file for checksumming instead of part of file.

Changes for v6.1.2 (2019-06-12)
===============================

Changes for v6.1.1 (2019-06-12)
===============================

CLI is using a blocksize that is different than upload. Changing to
match. Update manifest structure docs (#354)

Changes for v6.1.0 (2019-05-27)
===============================

-  Fix redirect logic when Retry-After is given with a 301 redirect
   (#341)

-  Logout application_secret flush (#342)

-  hca upload: Make sure checksum is computed after whole file is read
   not only the first/last bit. (#343)

Changes for v6.0.2 (2019-05-14)
===============================

-  Bump commonmark dependency (#340)

Changes for v6.0.1 (2019-05-10)
===============================

Fix: KeyError with manifests from production

Changes for v6.0.0 (2019-05-10)
===============================

Improve download parallelism (#296) Add paginate method. (#335) Include
version for naming downloaded bundle directory (#239) Enumerate
collections. (#330) Remote Login (#328) Add –layout option to manifest
download (#297) Reorganize dss client methods for clarity Bump dcplib
requirement version range Add Python 3.7 to Travis CI test matrix (#324)

Changes for v5.2.0 (2019-04-30)
===============================

-  Remove crcmod from direct dependencies (#323)

-  Connection pool size set to DEFAULT_THREAD_COUNT (#320)

-  Trufflehog fix. (#322)

-  SwaggerClient: set max redirects to a high number (#318)

Changes for v5.1.0 (2019-04-25)
===============================

uplaod: If a file has already been uploaded to a bucket, skip uploading
it if the sync argument is set to True (by default it is set to true).
(#306) upload: use smaller reads when doing client-side checksumming
Disable version checking until a better solution is found. (#315)

Changes for v5.0.2 (2019-04-24)
===============================

upload: fix prod url formatting for requests

Changes for v5.0.1 (2019-04-23)
===============================

upload: add some error verbosity for debugging purposes

Changes for v5.0.0 (2019-04-23)
===============================

Data Store
----------

-  Raise error if duplicate file is present (fixes #298)
-  Add download\_dir option (fixes #308)
-  Create Version Method (#304)
-  Handle bundle errors better; Fix test
-  Download bundles concurrently (#287)

Upload
------

-  Upload: covert Upload API to be object-based See classes
   UploadService and UploadArea
-  Expose the rest of the Upload API through UploadArea
-  Handle special characters in filenames

Changes for v4.10.0 (2019-04-05)
================================

-  Update bundle download to link to filestore (fixes #277) (#285)

-  Remove scandir dependency when it is included in Python (#289)

-  Add clientside checksumming in Upload Service CLI (#252)

Changes for v4.9.0 (2019-03-21)
===============================

Updating boto3 version since the previous 1.7-1.8 requirement is
incompatible with upload service. (#282) Centralize SECURITY.md, and
delete security.txt. (#281) Add a trufflehog regex check. (#283) Add
paths to manifest after v2 download (fixes #248) allow for not providing
slashes when selecting upload area (#280) Parellelize downloads for
manifest (fixes #236) Add version dir for manifest download (fixes #251)
Deduplicate file downloads (fixes #234) Bump tweak dependency to v1.0.2
(#271) Add security.txt. (#270) Amend retry counter placement.
Slash-Support : supporting '/' within upload/download for files in
bundles (#266) [Easy] Temporary fix to allow POST requests to be
retried. (#267) modified Error API (#225) Support get bundle iteration.
(#264) Properly place and print required vs. non-required args in the
help menu. Addresses #219. (#254) 301 retries are logged as info (#257)
Update README.rst Revert "Slash support (#247)" (#263) Revert "Update
README.rst" Slash-Support causing cli issues This reverts commit
a4fbe451028c64553ae11743f21db5e6b5cc957e. Slash support (#247) Update
README.rst Update README.rst Update README.rst Add readthedocs link to
the readme usage section. (#250) Check the CLI version. (#249) Add a
function to warn the user if the CLI version is out of date. (#246)
Adding GOOGLE\_APPLICATION\_CREDENTIALS to readme. (#242) puremagic <
1.5 (#245)

Changes for v4.8.0 (2019-02-22)
===============================

Revert “Relax boto range (#243)”

Changes for v4.7.0 (2019-02-21)
===============================

Relax boto range (#243) Support optional object parameters (#229) reduce
threads running on upload and reraise error from Tenacy on upload
methods (#228) Fixing the generation of DSS API Docs (#227) Update guide
for submitting data files to the DCP (#224)

Changes for v4.6.0 (2019-01-08)
===============================

enable file copy from s3 to upload area (#217) Apply log level to
requests and urllib3 (#216) Adding refresh-swagger command (#211)

Changes for v4.5.0 (2019-01-02)
===============================

post to upload api after successful file upload via hca cli (#214)
Updating test cases (#215) change retry lib and improve output from hca
upload tool during file upload (#208)

Changes for v4.4.10 (2018-11-19)
================================

-  Bumping version to sync with PyPI

Changes for v4.4.9 (2018-11-16)
===============================

removing redirect for retry_policy (#205) [CVE-2018-18074] Upgrade
requests to 2.20.0 (#204) Fixing read the docs error with markup
language in argsparser (#197) Remove redundant index on landing page
(#196) add testing for api_client (#190)

Changes for v4.4.8 (2018-09-27)
===============================

-  Initialize logging in hca.cli.main (#195)

Changes for v4.4.7 (2018-09-26)
===============================

Fix URL regexp in release script

Changes for v4.4.6 (2018-09-26)
===============================

-  Add release sanity checks

Changes for v4.4.1 (2018-09-20)
===============================

-  US 169 Add command line tool for checking upload area or file status
   (#187)

-  adding a backoff factor and retry redirects for api calls. (#184)

-  The life time of a token can be adjusted for authentication sessions.
   (#182)

Changes for v4.2.1 (2018-09-04)
===============================

-  Re-roll 4.2.0 due to a packaging issue.

Changes for v4.2.0 (2018-09-04)
===============================

-  Synchronize access to Swagger definition

-  Enable programmatic SwaggerClient host configuration (#142)

-  Allow for directory and file extension in hca upload files command
   (#174)

-  Restrict Boto3 dependency version range to 1.7.x (#176). Pin
   commonmark to 0.7.x.

-  upload cli parallelization 5x improvement (#155)

-  Add integration tests for SwaggerClient’s code generation methods
   (#109)

-  Help info for parameters appears in cli for upload and download
   (#146)

Changes for v4.1.4 (2018-08-07)
===============================

Fix ``hca upload file`` to work in production enironment again.

Changes for v4.1.3 (2018-08-06)
===============================

-  Use setuptools entry_points instead of scripts

-  Use s3 multipart constants as defined in dcplib (#150)

-  Documentation improvements

Changes for v4.1.2 (2018-07-27)
===============================

Fix ExpiredToken exceptions during ``hca upload file``

Changes for v4.1.1 (2018-07-27)
===============================

-  Update Google auth scopes to match new injected Google scope

-  Refetch DSS API definition weekly (#79) (#139)

-  Supply the required version to dss.upload (#135)


Changes for v4.0.0 (2018-06-20)
===============================

Upload: creds command and Python binding for get\_credentials Upload:
upload areas are now represented by a URI instead of URN DSS: fix
updated files seeping into downloads of older bundles

Changes for v3.5.2 (2018-06-04)
===============================

-  Resolve internal references in Swagger spec (#122)

Changes for v3.5.1 (2018-05-14)
===============================

-  Apply retry policy when fetching Swagger API definition

Changes for v3.5.0 (2018-05-03)
===============================

-  Add HTTP resume to DCP CLI download. (#101)

-  Cap the number of results for test_search (#111)

-  Provide schema for URLs. (#110)

-  Fix handling of enum values in JSON request bodies

Changes for v3.4.6 (2018-04-19)
===============================

-  Fix CLI parsers (#105)

Changes for v3.4.5 (2018-04-02)
===============================

-  Bump pyOpenSSL dependency on Python 2.7 (#102)

Changes for v3.4.4 (2018-04-02)
===============================

-  Fix version inlining

Changes for v3.4.3 (2018-04-02)
===============================

-  Add timeout policy for requests (#100)

-  Retry streaming read errors in bundle download (#98)

Changes for v3.4.2 (2018-03-30)
===============================

-  Retry on read errors. (#97)

Changes for v3.4.1 (2018-03-29)
===============================

-  Fix streaming managed download in DSS CLI

Changes for v3.4.0 (2018-03-29)
===============================

Use prod API endpoint by default

Changes for v3.3.1 (2018-03-15)
===============================

-  Enable Retry-After for HTTP 301 (#96)

-  Switch to checksumming_io from dcplib (#95)

Changes for v3.3.0 (2018-01-25)
===============================

upload: make upload\_service\_api\_url\_template configurable upload:
fix list command to work for areas with many files (#93) Bump tweak
dependency version (#92) Remove spurious line from autodoc file Send
DSS\_FAKE\_504\_PROBABILITY as a header.

Changes for v3.2.0 (2018-01-17)
===============================

Upload: Turn on S3 Transfer Acceleration by default Retry GET requests
(#87) Rename bundle\_id to bundle\_fqid (#86)

Changes for v3.1.1 (2018-01-03)
===============================

-  Add docs for config management options

-  Parameterize program name in Swagger client error message

-  Avoid wedging config when first run is performed offline

Changes for v3.1.0 (2017-12-14)
===============================

-  Use staging DSS by default

-  Fix typevar passthrough to argparse with typing.Optional kwargs

-  Upload: fix typo that prevented CRC32Cs being display in long
   listings

Changes for v3.0.5 (2017-12-06)
===============================

-  Fix handling of argument defaults in command line parsers

Changes for v3.0.4 (2017-12-04)
===============================

-  Fix regression in Upload CLI behavior, part 2

Changes for v3.0.3 (2017-12-04)
===============================

-  Fix regression in Upload CLI behavior

Changes for v3.0.2 (2017-12-04)
===============================

Fix structured exception printing on Python 2.7

Changes for v3.0.1 (2017-12-04)
===============================

-  Fix release

Changes for v3.0.0 (2017-12-04)
===============================

-  Refactor CLI to use new dynamic SwaggerClient utility class

-  Add structured error response data to exceptions

-  Documentation updates

-  New configuration manager

Changes for v2.3.2 (2017-11-21)
===============================

Fix incompatibility with older pip versions

Changes for v2.3.1 (2017-11-10)
===============================

Improved ``hca upload file`` determination of content-type.

Changes for v2.3.0 (2017-11-08)
===============================

More RFC-compliant support of media-type parameters. Upload dcp-type for
files defaults to "data". Fix: "upload list --long" now prints checksums
correctly. Loosen dependency requirements. "hca dss upload" sets S3
content-type when uploading to fake staging area.

Changes for v2.2.0 (2017-11-03)
===============================

New commands/python bindings: hca upload list - list your currently
selected upload area hca upload forget - remove knowledge of an upload
area Additional functionality: hca upload file: New optional argument
--quiet Now sets a dcp-type parameter on Content-Type when uploading.

Changes for v2.1.0 (2017-10-30)
===============================

Expose Python bindings for Upload Service

Changes for v2.0.0 (2017-10-18)
===============================

Rename 'staging' commands 'upload' Format the result, if any, in json if
--json-output is set. (#67)

Changes for v1.1.3 (2017-10-02)
===============================

Documentation updates.


Changes for v1.1.1 (2017-10-01)
===============================

Fix staging area credentials handling

Changes for v1.1.0 (2017-09-30)
===============================

Command: "hca staging select " Command: "hca staging areas" Command:
"hca staging upload <files" Command: "hca staging help"

Changes for v1.0.0 (2017-09-29)
===============================

Use "hca dss " to invoke DSS commands. Hardware DSS to use staging
deployment. Rename hca.api -> hca.dss. Rename query to es\_query (#58).

Changes for v0.11.0 (2017-09-12)
================================

Support async upload (#44)

Changes for v0.10.1 (2017-09-12)
================================

Fix broken mimetype sniffing logic (#51)

Changes for v0.10.0 (2017-08-17)
================================

Let readthedocs publish api spec (#38) Log to stderr and fix
Oauth2Client inputs

Changes for v0.9.5 (2017-08-16)
===============================

Stream printing to console & print bytes Jmackey popup auth Publish
python bindings to readthedocs

Changes for v0.9.3 (2017-08-04)
===============================

Removing popup capability to release functioning package.

Popups weren't working because client\_secrets.json is required and
wasn't being published with the package.

Changes for v0.9.2 (2017-08-04)
===============================

Add client\_secrets.json to MANIFEST directory.

Changes for v0.9.1 (2017-08-04)
===============================

Fix auto-path set Set config to ~/.config/hca/oauth2.json Reconfigure
auth to include sign-in pop-up if in a teletype

Changes for v0.9.0 (2017-08-02)
===============================

Full python binding support for all endpoints: \* bundles \* files \*
search \* subscriptions

CLI integration on top of these python bindings

Changes for v0.7.0 (2017-08-02)
===============================

Full python binding support for all endpoints: \* bundles \* files \*
search \* subscriptions

CLI integration on top of these python bindings

Changes for v0.7.3 (2017-08-01)
===============================

Add kwarg to redirect to different url.

Changes for v0.7.2 (2017-08-01)
===============================

Remove merge conflict lines.

Changes for v0.7.1 (2017-08-01)
===============================

Fix google auth request import

Changes for v0.7.0 (2017-08-01)
===============================

remove sign so I can release v0.7.0 remove tuple comprehension (python3
doesn't like that) Remove cli tests. Python bindings w/ auth and some
testing Autogenerated functions fully working. making abstractions a
package. Upload/Download refactor: Moved upload/download commands to
hca/api/abstractions dir. Release file resources after completed.
Cherry-picked upload-from-s3 changes Testing head\_files. Don't
regenerate python bindings. Templatize relative imports from
autogenerated. Remove unnecessary import Relative imports from
autogenerated Include all jinja files and update tests. Populate test
bundle with real data avoid namespace collision New python bindings
after positional args sorting. Sorted positional args to maintain
consistent order. Add jsonschema to install requirements. Add Jinja2 to
setup.py requirements. Generate fully functional python bindings with
docs attached. Remove .travis.yml changes b/c they landed on a pr that's
already been merged. Added region env variable to travis. Create classes
that add functions/parsers for each endpoint. (#20) Add AddedCommand
superclass for all api endpoints. (#19)

Changes for v0.7.0 (2017-08-01)
===============================

remove tuple comprehension (python3 doesn't like that) Remove cli tests.
Python bindings w/ auth and some testing Autogenerated functions fully
working. making abstractions a package. Upload/Download refactor: Moved
upload/download commands to hca/api/abstractions dir. Release file
resources after completed. Cherry-picked upload-from-s3 changes Testing
head\_files. Don't regenerate python bindings. Templatize relative
imports from autogenerated. Remove unnecessary import Relative imports
from autogenerated Include all jinja files and update tests. Populate
test bundle with real data avoid namespace collision New python bindings
after positional args sorting. Sorted positional args to maintain
consistent order. Add jsonschema to install requirements. Add Jinja2 to
setup.py requirements. Generate fully functional python bindings with
docs attached. Remove .travis.yml changes b/c they landed on a pr that's
already been merged. Added region env variable to travis. Create classes
that add functions/parsers for each endpoint. (#20) Add AddedCommand
superclass for all api endpoints. (#19)

Changes for v0.6.0 (2017-07-12)
===============================

Changes for v0.5.0 (2017-07-12)
===============================

Changes for v0.4.0 (2017-07-12)
===============================

Changes for v0.3.0 (2017-07-12)
===============================

v0.3.0 Support uploading bundle from staged s3 bucket to DSS. Fix upload
from local bug.

Changes for v0.3.0 (2017-07-12)
===============================

Support uploading bundle from staged s3 bucket to DSS. Fix bug in hca
upload.

Changes for v0.2.0 (2017-07-12)
===============================

-  Initial release.

Changes for v0.1.0 (2017-06-27)
===============================

-  Demo version pre-release

Command line interface that interacts with the Human Cell Atlas data
store REST API.

Current functionality: Retrieve or register a data file. Retrieve or
register a data bundle (collection of data files). Upload full directory
to cloud, register given files, and collect them into a bundle. Download
a bundle or file from HCA data store to local.

Changes for v1.0.0 (2017-06-26)
===============================

Changes for v0.0.8 (2017-06-06)
===============================

Test release
------------

Changes for v0.0.7 (2017-06-06)
===============================

Test release
------------

Changes for v0.0.6 (2017-06-06)
===============================

Test release
------------

Changes for v0.0.5 (2017-06-06)
===============================

Test release
------------

Changes for v0.0.4 (2017-06-06)
===============================

Test release
------------

Changes for v0.0.3 (2017-06-06)
===============================

Test Release
------------

Changes for v0.0.2 (2017-06-06)
===============================

Test release
------------

Changes for v0.0.1 (2017-06-06)
===============================

Test Release
------------

Changes for v0.0.1 (2017-06-06)
===============================

Test Release
------------

Changes for v0.0.1 (2017-06-06)
===============================

Test release
~~~~~~~~~~~~

