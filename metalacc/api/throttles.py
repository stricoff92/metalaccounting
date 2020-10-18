

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class NewAnonContactUsSubmissionThrottle(AnonRateThrottle):
    rate = "3/min"

class NewAuthedContactUsSubmissionThrottle(UserRateThrottle):
    rate = "3/min"

class NewRegistrationSubmissionThrottle(AnonRateThrottle):
    rate = "3/min"

class NewRegistrationDailySubmissionThrottle(AnonRateThrottle):
    rate = "6/day"
