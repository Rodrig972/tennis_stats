# Tennis Dashboard

## Description

This is a robust dashboard designed to analyze and visualize tennis player performance from ATP and WTA circuits. The application allows users to explore player statistics across different surfaces, tournaments, and years.

## Features

- Select ATP or WTA circuits.
- Choose seasons from 2014 to 2024.
- Analyze player performance by surfaces (Hard, Clay, Grass, Indoor).
- Include or exclude Grand Slam statistics.
- Interactive visualizations with Plotly.
- Select Favoris surface

## Prerequisites

- Python 3.8 or above.
- Ensure SQLite database files for ATP and WTA are present in the `Data_Base_Tennis/` directory.

## Installation

1. Clone the repository.

2. Navigate to the project directory.

3. Install dependencies using the following command:
   
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   
   ```bash
   streamlit run app.py
   ```

2. Follow the prompts in the sidebar to explore tennis player data.

## Project Structure

```
.
├── Data_Base_Tennis/
│   ├── atp_2024.db
│   ├── wta_2024.db
│   └── ...
├── main.py
├── requirements.txt
├── README.md
└── modules/
    ├── atp_module.py
    └── wta_module.py
    ├── atp_fav_surf.py
    └── wta_fav_surf.py
```

## Contributing

Feel free to fork the project and submit pull requests for improvements or additional features.

## License

This project is licensed under Rod LANDES License. See `LICENSE` for details.
