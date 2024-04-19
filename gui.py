import mysql.connector
import streamlit as st

# Establish a connection to the MySQL database
try:
    conn = mysql.connector.connect(
        host="mysql-salma.alwaysdata.net",
        user="salma",
        password="Salma_1234",
        database="salma_broadcasttv"
    )
    st.write("Connected to MySQL server")
except mysql.connector.Error as err:
    st.error(f"Error: {err}")
    st.stop()

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Display the query options to the user
user_input = st.selectbox(
    "Select a query:",
    [
        "User Registration",
        "Create a new favourite channel list",
        "Show all viewable channels from a specific location",
        "Show coverage of user's favourite channel list",
        "Show top 5 TV Networks",
        "Show top 5 Rockets by orbiting satellites",
        "Show top 5 growing satellites",
        "Show top 5 channels for each language",
        "Show channels by filters"
    ]
)

# Process user input
if user_input == "User Registration":
    st.subheader("Register a user")
    # Query to insert data into "userr" table
    query = "INSERT INTO userr (Username, Email, Location, Gender, Birthdate, Region) VALUES (%s, %s, %s, %s, %s, %s)"
    # Take input values from user for each column
    username = st.text_input("Enter username:")
    email = st.text_input("Enter email:")
    location = st.text_input("Enter location:")
    gender = st.text_input("Enter gender:")
    birthdate = st.text_input("Enter birthdate (YYYY-MM-DD):")
    region = st.text_input("Enter region:")
    if st.button("Register"):
        try:
            # Execute the query with input values
            cursor.execute(query, (username, email, location, gender, birthdate, region))
            conn.commit()  # Commit changes to the database
            st.success("Data inserted successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

elif user_input == "Create a new favourite channel list":
    st.subheader("Create a new list of favourite channels")
    # Ask user for username and number of channels to add
    username = st.text_input("Enter your username:")
    num_channels = st.number_input("Enter the number of channels to add:", min_value=1, value=1)

    # List to store channel names
    channel_names = []

    # Loop through and collect channel names
    for i in range(num_channels):
        channel_name = st.text_input(f"Enter the channel name {i + 1}:")
        channel_names.append(channel_name)

    # Button to add channels
    if st.button("Add Channels"):
        try:
            # Query to insert data into "favouritechannel" table
            query = "INSERT INTO favouritechannel (Username, ChannelName) VALUES (%s, %s)"
            # Execute inserts for all channel names in the list
            for channel_name in channel_names:
                cursor.execute(query, (username, channel_name))
            conn.commit()  # Commit changes to the database
            st.success(f"{num_channels} channels added to favorites successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")



elif user_input == "Show all viewable channels from a specific location":
    st.subheader("Channels viewable from location:")
    # Get the longitude of the location from the user
    location_longitude = st.number_input("Enter the longitude of the location:", value=0.0)

    if st.button("Show Channels"):
        # Construct the query to find channels viewable from the location
        query = f"""
            SELECT DISTINCT t.ChannelName
            FROM tvchannel t
            JOIN satellite s ON t.SatelliteName = s.SatelliteName
            WHERE s.PositionMag BETWEEN {location_longitude - 10} AND {location_longitude + 10}
        """

        try:
            # Execute the query
            cursor.execute(query)

            # Fetch all the results
            channels_viewable = cursor.fetchall()

            # Display the results
            if channels_viewable:
                st.write("Channels Viewable from Location:")
                for index, channel in enumerate(channels_viewable, start=1):
                    st.write(f"{index}. Channel Name: {channel[0]}")
            else:
                st.write("No channels found for the specified location.")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

elif user_input == "Show coverage of user's favourite channel list":
    st.subheader("Show user's favorite list coverage")

    # Get username from user input
    username = st.text_input("Enter your username:")

    if st.button("Show Coverage"):
        if not username:
            st.warning("Please enter a username.")
        else:
            # Fetch user's location
            location_query = f"""
                SELECT Location
                FROM userr
                WHERE Username = '{username}'
            """
            try:
                # Execute the query
                cursor.execute(location_query)
                user_location = cursor.fetchone()

                # Print the user's location
                if user_location:
                    user_location = int(user_location[0])  # Convert to integer
                    st.write(f"User '{username}' is located in: {user_location}")

                    # Drop the view if it exists
                    cursor.execute("DROP VIEW IF EXISTS UserSatelliteNames")

                    # Create a view for distinct SatelliteName values for user's channels
                    cursor.execute(f"""
                        CREATE VIEW UserSatelliteNames AS
                        SELECT DISTINCT SatelliteName
                        FROM tvchannel
                        WHERE ChannelName IN (
                            SELECT ChannelName
                            FROM favouritechannel
                            WHERE Username = '{username}'
                        )
                    """)

                    # Fetch positions for the fetched satellite names from the view
                    positions_query = f"""
                        SELECT SatelliteName, PositionMag
                        FROM satellite
                        WHERE SatelliteName IN (
                            SELECT SatelliteName
                            FROM UserSatelliteNames
                        )
                    """
                    cursor.execute(positions_query)
                    positions = cursor.fetchall()

                    # Initialize lists to store coverable and non-coverable satellites
                    coverable_satellites = []
                    non_coverable_satellites = []

                    # Check if user's location is coverable by satellites
                    for sat_name, position in positions:
                        position = int(position)
                        if position - 10 <= user_location <= position + 10:
                            coverable_satellites.append(sat_name)
                        else:
                            non_coverable_satellites.append(sat_name)

                    # Display coverable and non-coverable satellites
                    if coverable_satellites:
                        st.write("\nCoverable Satellites:")
                        for sat_name in coverable_satellites:
                            st.write(f"- {sat_name} (Coverable)")
                    else:
                        st.write("\nNo coverable satellites found.")

                    if non_coverable_satellites:
                        st.write("\nNon-Coverable Satellites:")
                        for sat_name in non_coverable_satellites:
                            st.write(f"- {sat_name} (Non-Coverable)")

                    # Fetch FrequencyMagnitude and Encryption for channels
                    broadcast_query = f"""
                        SELECT ChannelName, Frequency, Polarization, Encryptionn
                        FROM broadcasting
                        WHERE ChannelName IN (
                            SELECT ChannelName
                            FROM favouritechannel
                            WHERE Username = '{username}'
                        )
                    """
                    cursor.execute(broadcast_query)
                    channels_info = cursor.fetchall()

                    # Display channels' FrequencyMagnitude and Coverability
                    st.write("\nChannels Information:")
                    for channel_info in channels_info:
                        channel_name, freq_magnitude, polarization, encryption = channel_info
                        if encryption is None or encryption.lower() == "null":
                            st.write(f"- {channel_name}: Frequency Magnitude = {freq_magnitude}, Polarization: {polarization}, Encryption: {encryption} --> Coverable")
                        else:
                            st.write(f"- {channel_name}: Frequency Magnitude = {freq_magnitude}, Polarization: {polarization}, Encryption: {encryption} --> Not Coverable")
                else:
                    st.error(f"User '{username}' not found.")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")


elif user_input == "Show top 5 TV Networks":
    st.subheader("Top 5 TV Networks by Number of Channels and Average Number of Satellites per Channel")

    try:
        # Query to get the top 5 TV Networks by number of channels and average number of satellites
        query = """
            SELECT TvNetworkName, 
                COUNT(ChannelName) AS ChannelCount, 
                AVG(SatelliteCount) AS AvgSatellites
            FROM (
                SELECT 
                    TvNetworkName, 
                    ChannelName, 
                    COUNT(SatelliteName) AS SatelliteCount
                FROM tvchannel
                WHERE TvNetworkName IS NOT NULL AND TvNetworkName != 'None'
                GROUP BY TvNetworkName, ChannelName
            ) AS ChannelSatellites
            GROUP BY TvNetworkName
            ORDER BY ChannelCount DESC
            LIMIT 5
        """
        # Execute the query
        cursor.execute(query)

        # Fetch all the results
        top_5_networks = cursor.fetchall()

        # Display the results
        for index, network in enumerate(top_5_networks, start=1):
            st.write(f"{index}. TV Network: {network[0]}, Number of Channels: {network[1]}, Average Satellites per Channel: {network[2]}")

    except mysql.connector.Error as err:
        st.error(f"Error: {err}")

elif user_input == "Show top 5 Rockets by orbiting satellites":
    st.subheader("Top 5 Rockets by Number of Satellites")

    try:
        # Query to get the top 5 rockets by the number of satellites they put in orbit
        query = """
            SELECT LaunchingRocket, COUNT(SatelliteName) AS SatelliteCount
            FROM satellite
            GROUP BY LaunchingRocket
            ORDER BY SatelliteCount DESC
            LIMIT 5
        """
        # Execute the query
        cursor.execute(query)

        # Fetch all the results
        top_5_rockets = cursor.fetchall()

        # Display the results
        for index, rocket in enumerate(top_5_rockets, start=1):
            st.write(f"{index}. {rocket[0]} - {rocket[1]} satellites")

    except mysql.connector.Error as err:
        st.error(f"Error: {err}")


elif user_input == "Show top 5 growing satellites":
    st.subheader("Top 5 Growing Satellites")

    try:
        # Query to get the top 5 growing satellites by the number of channels they host
        query = """
            SELECT s.SatelliteName, s.LaunchDate, COUNT(c.ChannelName) AS ChannelCount
            FROM satellite s
            JOIN tvchannel c ON s.SatelliteName = c.SatelliteName
            GROUP BY s.SatelliteName, s.LaunchDate
            ORDER BY s.LaunchDate DESC, ChannelCount 
            LIMIT 5
        """
        # Execute the query
        cursor.execute(query)

        # Fetch all the results
        top_5_growing_satellites = cursor.fetchall()

        # Display the results
        for index, satellite in enumerate(top_5_growing_satellites, start=1):
            st.write(f"{index}. Satellite Name: {satellite[0]}, Launch Date: {satellite[1]}, Number of Channels: {satellite[2]}")

    except mysql.connector.Error as err:
        st.error(f"Error: {err}")


elif user_input == "Show top 5 channels for each language":
    st.subheader("Top 5 Channels for Each Language by Number of Satellites Hosted")

    try:
        # Execute the query
        query = """
            SELECT Lang, ChannelName, SatelliteCount
            FROM (
                SELECT 
                    Lang,
                    ChannelName,
                    COUNT(SatelliteName) AS SatelliteCount,
                    ROW_NUMBER() OVER (PARTITION BY Lang ORDER BY COUNT(SatelliteName) DESC) AS rank
                FROM tvchannel
                GROUP BY Lang, ChannelName
            ) AS ChannelSatellites
            WHERE rank <= 5
        """
        cursor.execute(query)
        top_channels_by_language = cursor.fetchall()

        # Display the results
        if top_channels_by_language:
            # Display user input for languages
            languages_input = st.text_input("Enter the languages you want to filter (comma-separated):")
            languages = [lang.strip() for lang in languages_input.split(',')]

            # Filter rows based on user-specified languages
            filtered_channels = [channel for channel in top_channels_by_language if channel[0] in languages]

            # Display filtered results
            if filtered_channels:
                for index, channel in enumerate(filtered_channels, start=1):
                    st.write(f"{index}. Language: {channel[0]}, Channel: {channel[1]}, Number of Satellites: {channel[2]}")
            else:
                st.write("No channels found for the specified languages.")
        else:
            st.write("No data available.")
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")


elif user_input == "Show channels by filters":
    st.subheader("Filtered Channels")

    # Get filter criteria from the user
    region = st.text_input("Enter region (leave empty to skip):").strip()
    satellite = st.text_input("Enter satellite (leave empty to skip):").strip()
    hd_sd = st.text_input("Enter HD/SD (HD/SD/leave empty to skip):").strip()
    language = st.text_input("Enter language (leave empty to skip):").strip()

    # Construct the base query
    query = """
        SELECT t.ChannelName, t.Lang AS Language, b.Video AS HD_SD, s.Region AS Region, t.SatelliteName AS Satellite
        FROM tvchannel t
        LEFT JOIN broadcasting b ON t.ChannelName = b.ChannelName
        LEFT JOIN satellite s ON t.SatelliteName = s.SatelliteName
        WHERE 1
    """

    # Add filters based on user input
    if region:
        query += f" AND s.Region = '{region}'"
    if satellite:
        query += f" AND t.SatelliteName = '{satellite}'"
    if hd_sd:
        query += f" AND b.Video LIKE '%{hd_sd}%'"
    if language:
        query += f" AND t.Lang = '{language}'"

    try:
        # Execute the query
        cursor.execute(query)

        # Fetch all the results
        filtered_channels = cursor.fetchall()

        # Display the results
        for index, channel in enumerate(filtered_channels, start=1):
            st.write(f"{index}. Channel Name: {channel[0]}, Language: {channel[1]}, HD/SD: {channel[2]}, Region: {channel[3]}, Satellite: {channel[4]}")

    except mysql.connector.Error as err:
        st.error(f"Error: {err}")


# Close cursor and connection
cursor.close()
conn.close()
