

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class NewAnonContactUsSubmissionThrottle(AnonRateThrottle):
    rate = "3/min"

class NewAuthedContactUsSubmissionThrottle(UserRateThrottle):
    rate = "3/min"

class NewRegistrationSubmissionThrottle(AnonRateThrottle):
    rate = "3/min"
