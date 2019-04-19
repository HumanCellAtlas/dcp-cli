from collections import defaultdict

from hca.upload.lib.api_client import ApiClient


class UploadAreaFilesStatusCheck(object):
    def __init__(self, env):
        self.upload_api_client = ApiClient(env)

    def get_file_statuses(self, upload_area_uuid):
        checksum_statuses = self.upload_api_client.checksum_statuses(upload_area_uuid)
        validation_statuses = self.upload_api_client.validation_statuses(upload_area_uuid)

        validated_file_total = 0
        for status in validation_statuses:
            validated_file_total += validation_statuses[status]
        validation_statuses['VALIDATION_UNSCHEDULED'] = checksum_statuses['CHECKSUMMED'] - validated_file_total

        return checksum_statuses, validation_statuses

    def check_file_statuses(self, upload_area_uuid, output_file_name):
        checksum_statuses, validation_statuses = self.get_file_statuses(upload_area_uuid)

        self.generate_report(upload_area_uuid, output_file_name, checksum_statuses, validation_statuses)

    def generate_report(self, upload_area, output_file_name, checksum_statuses, validation_statuses):
        f = open("{}.txt".format(output_file_name), "w+")
        f.write('FILE STATUS REPORT\n'
                'UploadArea: {}\n'
                'Total Number of Files: {}\n'
                'CHECKSUMS\n'.format(upload_area, checksum_statuses["TOTAL_NUM_FILES"]))
        del checksum_statuses['TOTAL_NUM_FILES']
        for category in sorted(checksum_statuses):
            f.write("\t{} files: {}\n".format(category, checksum_statuses[category]))
        f.write('VALIDATIONS\n')
        for category in sorted(validation_statuses):
            f.write("\t{} files: {}\n".format(category, validation_statuses[category]))
        f.close()


class FileStatusCheck(object):
    def __init__(self, env):
        self.upload_api_client = ApiClient(env)

    def get_checksum_status(self, upload_area, file_id):
        try:
            response = self.upload_api_client.checksum_status(upload_area, file_id)
        except RuntimeError as e:
            return 'CHECKSUM_STATUS_RETRIEVAL_ERROR: {}'.format(e)
        checksum_status = response['checksum_status']
        if checksum_status == 'SCHEDULED':
            return 'CHECKSUMMING_SCHEDULED'
        elif checksum_status == 'UNSCHEDULED':
            return 'CHECKSUMMING_UNSCHEDULED'
        else:
            return checksum_status

    def get_validation_status(self, upload_area, file_id):
        try:
            response = self.upload_api_client.validation_status(upload_area, file_id)
        except RuntimeError as e:
            return 'VALIDATION_STATUS_RETRIEVAL_ERROR: {}'.format(e)
        validation_status = response['validation_status']
        if validation_status == 'SCHEDULED':
            return 'VALIDATION_SCHEDULED'
        elif validation_status == 'UNSCHEDULED':
            return 'VALIDATION_UNSCHEDULED'
        else:
            return validation_status

    def check_file_status(self, upload_area, file_id):
        checksum_status = self.get_checksum_status(upload_area, file_id)
        if checksum_status != 'CHECKSUMMED':
            return checksum_status
        validation_status = self.get_validation_status(upload_area, file_id)
        return validation_status
