<?php
include 'mak.php'
header('Content-Type: application/json'); //Return JSON
// MySQL database connection details
$response = ['success' => false, 'message' => "", 'student_id' => '', 'image' => '', 'mime_type'=> ''];

$host = 'localhost'; // Your database host
$dbname = 'test_db2'; // The database you created earlier
$username = 'root'; // Your MySQL username
$password = ''; // Your MySQL password (empty in this case)

try {
    // Create a connection to MySQL
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Check if parameters are provided
    if (isset($_POST['student_id']) && isset($_POST['password'])) {
        $student_id = trim($_POST['student_id']);
        $password = trim($_POST['password']); // In production, use $_POST

        // Basic validation
        if (empty($student_id) || empty($password)) {
            $response['message']= "Please provide all information.";
        }

        // Prepare and execute the SQL query to fetch password hash and image data from 'users' table
        $stmt = $pdo->prepare("SELECT student_id, password, image_data, mime_type FROM users WHERE student_id = :student_id");
        $stmt->bindValue(':student_id', $student_id, PDO::PARAM_STR);
        $stmt->execute();
        $row = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($row && password_verify($password, $row['password'])) {
            // Credentials valid, retrieve image data and MIME type
           $response['success'] = true;
	   $response['message'] = "Login successful";
           $response['student_id'] = $row['student_id'];

            if (!empty($row['image_data'])) {
                // Serve the image directly with correct headers
                $response['image'] = base64_encode($row['image_data']);
                $response['mime_type'] = $row['mime_type'];
            } else {
                $response['message']=  "Verified, but no valid image data found.";
            }
        } else {
            $response['message']= "Invalid Credentials.";
        }
    } else {
        $response['message']= "Please provide all information.";
    }
} catch (PDOException $e) {
   $response['message']=  "Database error: " . $e->getMessage();
}

echo json_encode($response);
$pdo = null;
?>