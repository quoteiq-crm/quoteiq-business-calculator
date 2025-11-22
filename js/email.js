// QuoteIQ ROI Calculator - Email Capture

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Email capture initialized');

    // Get email form elements
    const emailForm = document.getElementById('emailCaptureForm');
    const emailInput = document.getElementById('userEmail');
    const emailBtn = document.getElementById('emailBtn');

    // Check if email form exists (only on main page with results)
    if (!emailForm) {
        console.log('Email form not found on this page');
        return;
    }

    // Email form submission handler
    emailForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Email form submitted');

        // Get email value
        const email = emailInput.value.trim();

        // Validate email format
        if (!validateEmail(email)) {
            alert('Please enter a valid email address');
            return;
        }

        // Get data from localStorage
        const calculatorResults = localStorage.getItem('calculatorResults');
        const formData = localStorage.getItem('formData');

        if (!calculatorResults || !formData) {
            alert('Calculation results not found. Please calculate your ROI first.');
            return;
        }

        // Parse stored data
        const results = JSON.parse(calculatorResults);
        const inputs = JSON.parse(formData);

        console.log('Sending email with data:', { email, results, inputs });

        // Send data to Formspree
        sendToFormspree(email, inputs, results);
    });

    /**
     * Validate email format
     * @param {string} email - Email address to validate
     * @returns {boolean} - True if valid email format
     */
    function validateEmail(email) {
        // Simple but effective email regex
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Send data to Formspree
     * @param {string} email - User's email address
     * @param {object} inputs - Form input data
     * @param {object} results - Calculation results
     */
    function sendToFormspree(email, inputs, results) {
        // Show loading state
        setLoadingState(true);

        // Prepare data payload
        const payload = {
            email: email,
            timestamp: new Date().toISOString(),
            subject: 'QuoteIQ ROI Calculator - Your Business Savings Report',
            inputs: {
                quotesPerWeek: inputs.quotesPerWeek,
                minutesPerQuote: inputs.minutesPerQuote,
                avgJobValue: inputs.avgJobValue,
                conversionRate: inputs.conversionRate,
                hourlyRate: inputs.hourlyRate,
                paymentDelay: inputs.paymentDelay,
                hoursOnPayments: inputs.hoursOnPayments
            },
            results: {
                hoursPerWeekQuoting: results.hoursPerWeekQuoting,
                hoursPerYearQuoting: results.hoursPerYearQuoting,
                costOfQuotingTime: results.costOfQuotingTime,
                lostJobs: results.lostJobs,
                lostRevenue: results.lostRevenue,
                paymentHoursPerYear: results.paymentHoursPerYear,
                costOfPaymentTime: results.costOfPaymentTime,
                totalAnnualCost: results.totalAnnualCost,
                netSavings: results.netSavings,
                roi: results.roi,
                timeSavedPerWeek: results.timeSavedPerWeek,
                improvedConversionRate: results.improvedConversionRate
            }
        };

        // Formspree endpoint (placeholder - update with real endpoint)
        const formspreeEndpoint = 'https://formspree.io/f/PLACEHOLDER';

        console.log('Sending to Formspree:', payload);

        // Send POST request to Formspree
        fetch(formspreeEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            console.log('Formspree response status:', response.status);

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            return response.json();
        })
        .then(data => {
            console.log('Formspree success:', data);
            handleSuccess(email);
        })
        .catch(error => {
            console.error('Formspree error:', error);
            handleError(error);
        })
        .finally(() => {
            setLoadingState(false);
        });
    }

    /**
     * Set loading state on button
     * @param {boolean} isLoading - Loading state
     */
    function setLoadingState(isLoading) {
        if (isLoading) {
            emailBtn.disabled = true;
            emailBtn.innerHTML = '🔄 Sending...';
            emailBtn.classList.add('opacity-75', 'cursor-not-allowed');
        } else {
            emailBtn.disabled = false;
            emailBtn.innerHTML = '📧 Email Me My Full Report';
            emailBtn.classList.remove('opacity-75', 'cursor-not-allowed');
        }
    }

    /**
     * Handle successful email submission
     * @param {string} email - User's email address
     */
    function handleSuccess(email) {
        console.log('Email sent successfully to:', email);

        // Show success message
        showSuccessMessage();

        // Store email in localStorage for thank-you page
        localStorage.setItem('userEmail', email);

        // Redirect to thank-you page after 2 seconds
        setTimeout(() => {
            window.location.href = `thank-you.html?email=${encodeURIComponent(email)}`;
        }, 2000);
    }

    /**
     * Show success message
     */
    function showSuccessMessage() {
        // Replace form with success message
        const formContainer = emailForm.parentElement;
        formContainer.innerHTML = `
            <div class="text-center py-8">
                <div class="text-6xl mb-4">✅</div>
                <h3 class="text-2xl font-bold text-green-600 mb-2">
                    Check your email!
                </h3>
                <p class="text-gray-700 mb-4">
                    Your report is on its way.
                </p>
                <p class="text-sm text-gray-500">
                    Redirecting you to confirmation page...
                </p>
            </div>
        `;
    }

    /**
     * Handle error during submission
     * @param {Error} error - Error object
     */
    function handleError(error) {
        console.error('Email submission error:', error);

        // Show error alert
        alert('Oops! Something went wrong. Please try again or contact us directly.');
    }
});
