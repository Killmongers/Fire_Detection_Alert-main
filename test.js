const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: 'moolyaswastik48@gmail.com',
    pass: 'htjf errw gzau ktlg' // Replace with your email password or App Password
  }
});

const mailOptions = {
  from: 'moolyaswastik48@gmail.com',
  to: 'moolyaswastik48@gmail.com', // Replace with a real recipient email
  subject: 'Test Email',
  text: 'This is a test email from Nodemailer.'
};

transporter.sendMail(mailOptions, (error, info) => {
  if (error) {
    console.error('Error details:', error);
  } else {
    console.log('Email sent:', info.response);
  }
});
