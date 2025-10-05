export const FORM_FIELDS = {
  name: {
    label: 'Full Name',
    type: 'text',
    required: true,
    placeholder: 'Enter your full name',
    validation: {
      minLength: 2,
      maxLength: 50,
      pattern: /^[a-zA-Z\s]+$/,
      message: 'Name must contain only letters and spaces'
    }
  },
  date: {
    label: 'Date of Birth',
    type: 'date',
    required: true,
    validation: {
      min: '1900-01-01',
      max: '2100-12-31',
      message: 'Please enter a valid date between 1900-2100'
    }
  },
  time: {
    label: 'Time of Birth',
    type: 'time',
    required: true,
    format: '12h',
    validation: {
      message: 'Please enter a valid time'
    }
  },
  place: {
    label: 'Place of Birth',
    type: 'autocomplete',
    required: true,
    placeholder: 'Start typing city name...',
    validation: {
      minLength: 2,
      message: 'Please select a valid place'
    }
  }
};

export const VALIDATION_MESSAGES = {
  required: 'This field is required',
  invalidDate: 'Please enter a valid date',
  invalidTime: 'Please enter a valid time',
  invalidPlace: 'Please select a valid place from suggestions',
  networkError: 'Network error. Please try again.',
  serverError: 'Server error. Please try again later.'
};