from .upload_area import UploadArea


def list_areas():
    return [{'uuid': area.uuid, 'is_selected': area.is_selected} for area in UploadArea.all()]
