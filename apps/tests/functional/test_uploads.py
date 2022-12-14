from datetime import date, timedelta
import json
import os
from apps.authentication.box_jwt import jwt_check_client
from apps.booking.demo_folders import booking_diver_folder_get, booking_folder_get
from apps.booking.models import Booking, Booking_Diver, Diver
from apps.booking.booking import booking_from_data
from apps.booking.waiver import booking_diver_waiver_sign
from boxsdk import BoxAPIException


def test_booking_folder_get(
    test_client, init_database, new_diver_john, new_diver_jane, login_user
):
    """
    GIVEN a booking
    WHEN the app needs to upload a file to the diver folder
    THEN system must have created the folder structure
    AND return the folder for this specific diver booking
    """

    book_date = date.today() + timedelta(days=10)
    booking = booking_from_data(1, book_date, new_diver_john.name, new_diver_john.email,1)
    booking_diver = Booking_Diver.query.filter_by(booking_id=booking.id).first()

    assert booking is not None

    booking_folder_id = booking_folder_get(booking.id)

    assert booking_folder_id is not None

    booking_diver_folder_id = booking_diver_folder_get(booking_diver.id)

    assert booking_diver_folder_id is not None

    # delete the folder
    client = jwt_check_client()

    client.folder(booking_diver_folder_id).delete()

    # get the folder again
    booking_diver_folder_id = booking_diver_folder_get(booking_diver.id)

    try:
        folder = client.folder(booking_diver_folder_id).get()

    except BoxAPIException as e:
        assert e.status == 404
        assert False

    assert folder is not None


def test_booking_details(
    test_client, init_database, new_diver_john, new_diver_jane, login_user
):
    """
    GIVEN an upload page
    WHEN redered
    THEN show booking details
    """

    book_date = date.today() + timedelta(days=10)
    booking_from_data(1, book_date, new_diver_jane.name, new_diver_jane.email,1)
    booking = booking_from_data(1, book_date, new_diver_john.name, new_diver_john.email,1)

    assert booking is not None

    booking = Booking.query.order_by(Booking.id.desc()).first()
    response = test_client.get(
        "/booking/"+str(booking.id),
        follow_redirects=True,
    )

    assert response.status_code == 200  or response.status_code == 308

    assert b"Certification" in response.data

    assert b"Insurance" in response.data

    assert b"Waiver" in response.data


def test_booking_upload_event_cert(
    test_client, init_database, new_diver_john, new_diver_jane, login_user
):
    """
    GIVEN the event to upload a certification file to the booking_diver folder
    WHEN posted with a valid upload event and a valid file
    THEN update the booking_diver certification with the file id
    """

    book_date = date.today() + timedelta(days=10)
    # booking_from_data(1,book_date,new_diver_jane.name,new_diver_jane.email)
    booking = booking_from_data(1, book_date, new_diver_john.name, new_diver_john.email,1)
    booking_diver = Booking_Diver.query.filter_by(booking_id=booking.id).first()
    diver = Diver.query.filter_by(email=new_diver_john.email).first()
    bd_id = booking_diver.id

    assert booking is not None

    booking_folder_id = booking_folder_get(booking.id)

    assert booking_folder_id is not None

    booking_diver_folder_id = booking_diver_folder_get(booking_diver.id)

    assert booking_diver_folder_id is not None
    assert booking_diver.certification_file_id is None

    client = jwt_check_client()

    # create a file

    base_path = os.path.abspath(os.getcwd())
    file_path = os.path.join(base_path, "apps/tests/files/Padi-Scuba-Card.jpg")
    file_name = "CERT-" + diver.name + ".jpg"

    try:
        new_file = client.folder(booking_diver.folder_id).upload(
            file_path=file_path, file_name=file_name
        )
    except BoxAPIException as error:
        first_conflict = error.context_info["conflicts"]

        if first_conflict["type"] == "file":
            new_file = client.file(first_conflict["id"]).get()

    assert new_file is not None

    data = {
        "eventType": "complete",
        "documentType": "CERTIFICATE",
        "booking_diver_id": booking_diver.id,
        "e": [
            {
                "type": "file",
                "id": new_file.id,
            }
        ],
    }

    response = test_client.post(
        "/event/upload/",
        data=json.dumps(data),
        follow_redirects=False,
        content_type="application/json",
    )

    assert response.status_code == 200

    booking_diver = Booking_Diver.query.filter_by(id=bd_id).first()

    assert booking_diver.certification_file_id == new_file.id
    assert booking_diver.certification_task_id is not None

    # check if task was created
    cert_task = client.task(booking_diver.certification_task_id).get()

    file_tasks = client.file(booking_diver.certification_file_id).get_tasks()

    assert file_tasks is not None


def test_booking_upload_event_insurance(
    test_client, init_database, new_diver_john, new_diver_jane, login_user
):
    """
    GIVEN the event to upload an insurance file to the booking_diver folder
    WHEN posted with a valid upload event and a valid file
    THEN update the booking_diver insurance with the file id
    """

    book_date = date.today() + timedelta(days=10)
    # booking_from_data(1,book_date,new_diver_jane.name,new_diver_jane.email)
    booking = booking_from_data(1, book_date, new_diver_john.name, new_diver_john.email,1)
    booking_diver = Booking_Diver.query.filter_by(booking_id=booking.id).first()
    diver = Diver.query.filter_by(email=new_diver_john.email).first()
    bd_id = booking_diver.id

    assert booking is not None

    booking_folder_id = booking_folder_get(booking.id)

    assert booking_folder_id is not None

    booking_diver_folder_id = booking_diver_folder_get(booking_diver.id)

    assert booking_diver_folder_id is not None
    assert booking_diver.insurance_file_id is None

    client = jwt_check_client()

    # create a file

    base_path = os.path.abspath(os.getcwd())
    file_path = os.path.join(base_path, "apps/tests/files/Dan-Insurance-Card.jpg")
    file_name = "INSURE-" + diver.name + ".jpg"

    try:
        new_file = client.folder(booking_diver.folder_id).upload(
            file_path=file_path, file_name=file_name
        )
    except BoxAPIException as error:
        first_conflict = error.context_info["conflicts"]

        if first_conflict["type"] == "file":
            new_file = client.file(first_conflict["id"]).get()

    assert new_file is not None

    data = {
        "eventType": "complete",
        "documentType": "INSURANCE",
        "booking_diver_id": booking_diver.id,
        "e": [
            {
                "type": "file",
                "id": new_file.id,
            }
        ],
    }

    response = test_client.post(
        "/event/upload/",
        data=json.dumps(data),
        follow_redirects=False,
        content_type="application/json",
    )

    assert response.status_code == 200

    booking_diver = Booking_Diver.query.filter_by(id=bd_id).first()

    assert booking_diver.insurance_file_id == new_file.id
    assert booking_diver.insurance_task_id is not None

    # check if task was created
    cert_task = client.task(booking_diver.insurance_task_id).get()

    file_tasks = client.file(booking_diver.insurance_file_id).get_tasks()

    assert file_tasks is not None


def test_sign(test_client, init_database, new_diver_barbas, login_user):
    """
    GIVEN a booking diver id
    WHEN a waiver sign is requested
    THEN a sign request is created
    """

    book_date = date.today() + timedelta(days=10)
    booking = booking_from_data(
        1, book_date, new_diver_barbas.name, new_diver_barbas.email, 1
    )
    booking_diver = Booking_Diver.query.filter_by(booking_id=booking.id).first()
    diver = Diver.query.filter_by(email=new_diver_barbas.email).first()
    bd_id = booking_diver.id

    assert booking is not None

    booking_folder_id = booking_folder_get(booking.id)

    assert booking_folder_id is not None

    booking_diver_folder_id = booking_diver_folder_get(booking_diver.id)

    assert booking_diver_folder_id is not None

    # Create a waiver sign request
    client = jwt_check_client()

    sign_request = booking_diver_waiver_sign(bd_id)

    sign_request_check = client.sign_request(sign_request_id=sign_request.id)

    assert sign_request == sign_request_check

    booking_diver = Booking_Diver.query.filter_by(id=bd_id).first()

    assert booking_diver.waiver_file_id == sign_request.sign_files["files"][0].id
