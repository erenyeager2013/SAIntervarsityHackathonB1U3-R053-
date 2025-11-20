<?php
// Database connection details
$host = 'localhost'; // Your database host
$dbname = 'test_db2'; // Name of the database
$username = 'root'; // Your database username
$password = ''; // Your database password

// Create a connection to MySQL
try {
    $pdo = new PDO("mysql:host=$host", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Create the database if it does not exist
    $pdo->exec("CREATE DATABASE IF NOT EXISTS $dbname");
    echo "Database created or already exists\n";

    // Select the database
    $pdo->exec("USE $dbname");

    // Create table if it does not exist
    $tableQuery = "
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        image_data LONGBLOB,
        mime_type VARCHAR(255)
    )";
    $pdo->exec($tableQuery);
    echo "Table created or already exists\n";

    // Sample data
    $testUsername = 'john_doe';
    $testPassword = 'testpassword123'; // Password to be hashed
    $testImageData = base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAwAB/AN19FNsAAAAASUVORK5CYII='); // Base64-encoded 1x1 PNG image
    $testMimeType = 'image/png'; // MIME type for the image

    // Hash the password
    $hashedPassword = password_hash($testPassword, PASSWORD_DEFAULT);

    // Prepare SQL to insert the test data
    $insertQuery = "
    INSERT INTO users (student_id, password, image_data, mime_type)
    VALUES (:student_id, :password, :image_data, :mime_type)";

    $stmt = $pdo->prepare($insertQuery);
    $stmt->bindParam(':student_id', $testUsername);
    $stmt->bindParam(':password', $hashedPassword);
    $stmt->bindParam(':image_data', $testImageData, PDO::PARAM_LOB); // Store image as a blob
    $stmt->bindParam(':mime_type', $testMimeType);

    // Execute the query
    $stmt->execute();
    echo "Test user inserted successfully\n";

} catch (PDOException $e) {
    echo "Error: " . $e->getMessage();
}

// Close the connection
$pdo = null;
?>
