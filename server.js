const express = require('express');
const nodemailer = require('nodemailer');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

// Configure nodemailer transporter
const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: 'moolyaswastik48@gmail.com', // Replace with your email
    pass: 'htjf errw gzau ktlg' // Replace with your email password or App Password
  }
});

// Email sending endpoint
app.post('/send-email', (req, res) => {
  const { to, subject, text } = req.body;

  const mailOptions = {
    from: 'moolyaswastik48@gmail.com',
    to:'moolyaswastik48@gmail.com',
    subject:'Fire Alert',
    text:'Warning: A fire accident has been reported!'
  };

  transporter.sendMail(mailOptions, (error, info) => {
    if (error) {
      console.error('Error details:', error); // Log detailed error information
      res.status(500).send('Error sending email');
    } else {
      console.log('Email sent: ' + info.response);
      res.status(200).send('Email sent');
    }
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
