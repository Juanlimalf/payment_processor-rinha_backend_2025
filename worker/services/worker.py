from services.tasks import payment_process


def task(data):
    payment_process(data=data)
