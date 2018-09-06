
class UploadAreaFilesStatusCheck(object):
    def get_upload_area(self, submission_id):
        pass
        # How to implement this step?

    def get_file_list(self, upload_area):
        pass

    def check_all_file_statuses(self, upload_area):
        file_list = self.get_file_list(upload_area)
        for file in file_list:
            status = FileStatusCheck.check_file_status(upload_area, file)
            ## WHAT TO DO WITH FILE STATUSES?
                # print individually in terminal
                # concat and return a list with id?

class FileStatusCheck(object):
    def get_checksum_status(self, upload_area, file_id):
        return 'CHECKSUMMED'

    def get_validation_status(self, upload_area, file_id):
        return 'VALIDATED'

    def get_notification_status(self, upload_area, file_id):
        return 'NOTIFIED'

    def check_file_status(self, upload_area, file_id):
        checksum_status = self.get_checksum_status(upload_area, file_id)
        if checksum_status != 'CHECKSUMMED':
            return f"File {upload_area}/{file_id} is currently being checksummed. Status is: {checksum_status}"

        validation_status = self.get_validation_status(upload_area, file_id)
        if validation_status != 'VALIDATED':
            return f"File {upload_area}/{file_id} is currently being validated. Status is: {validation_status}"

        notification_status = self.get_notification_status(upload_area, file_id)
        if notification_status != 'DELIVERED':
            return f"File {upload_area}/{file_id} has been checksummed and validated. Notification status is: {notification_status} "

        return f"File {upload_area}/{file_id} has been checksummed and validated. Ingest has been notified"
