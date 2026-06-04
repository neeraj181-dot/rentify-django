"""Indian states and major cities for listing location fields."""

INDIAN_STATES = [
    ('', 'Select state'),
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Maharashtra', 'Maharashtra'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Delhi', 'Delhi'),
    ('Gujarat', 'Gujarat'),
    ('Rajasthan', 'Rajasthan'),
    ('West Bengal', 'West Bengal'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Punjab', 'Punjab'),
    ('Haryana', 'Haryana'),
    ('Goa', 'Goa'),
    ('Other', 'Other'),
]

CITIES_BY_STATE = {
    'Kerala': [
        'Malappuram', 'Kochi', 'Kottayam', 'Kozhikode', 'Calicut',
        'Thiruvananthapuram', 'Trivandrum', 'Thrissur', 'Palakkad', 'Alappuzha',
    ],
    'Karnataka': ['Bangalore', 'Bengaluru', 'Mysuru', 'Mangalore', 'Hubli'],
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Trichy', 'Salem'],
    'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Nashik', 'Thane'],
    'Telangana': ['Hyderabad', 'Warangal', 'Karimnagar'],
    'Delhi': ['New Delhi', 'Delhi'],
    'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot'],
}
