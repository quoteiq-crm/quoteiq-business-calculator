// QuoteIQ ROI Calculator - Calculator Logic

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Calculator initialized');

    // Get form and button elements
    const form = document.getElementById('calculatorForm');
    const calculateBtn = document.getElementById('calculateBtn');
    const recalculateBtn = document.getElementById('recalculateBtn');
    const resultsSection = document.getElementById('results');

    // Form submission handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Form submitted');

        // Validate and get all input values
        if (!validateForm()) {
            return;
        }

        // Get input values
        const formData = getFormData();
        console.log('Form data:', formData);

        // Perform calculations
        const results = calculateROI(formData);
        console.log('Calculation results:', results);

        // Store results in localStorage
        localStorage.setItem('calculatorResults', JSON.stringify(results));
        console.log('Results stored in localStorage');

        // Display results
        displayResults(results);

        // Show results section and scroll to it
        resultsSection.classList.remove('hidden');
        setTimeout(() => {
            smoothScrollTo(resultsSection);
        }, 100);
    });

    // Recalculate button handler
    recalculateBtn.addEventListener('click', function() {
        console.log('Recalculate clicked');
        smoothScrollTo(document.getElementById('calculator-form'));
    });

    /**
     * Validate all form fields
     * @returns {boolean} - True if form is valid
     */
    function validateForm() {
        // Get all input values
        const quotesPerWeek = document.getElementById('quotesPerWeek').value;
        const minutesPerQuote = document.getElementById('minutesPerQuote').value;
        const avgJobValue = document.getElementById('avgJobValue').value;
        const conversionRate = document.getElementById('conversionRate').value;
        const hourlyRate = document.getElementById('hourlyRate').value;
        const paymentDelay = document.querySelector('input[name="paymentDelay"]:checked');
        const hoursOnPayments = document.getElementById('hoursOnPayments').value;

        // Check if all fields are filled
        if (!quotesPerWeek || !minutesPerQuote || !avgJobValue || !conversionRate || !hourlyRate || !hoursOnPayments) {
            alert('Please fill out all fields');
            return false;
        }

        // Check if payment delay is selected
        if (!paymentDelay) {
            alert('Please select payment delay option');
            return false;
        }

        // Validate all numbers are positive
        if (quotesPerWeek <= 0 || minutesPerQuote <= 0 || avgJobValue <= 0 ||
            conversionRate <= 0 || hourlyRate <= 0 || hoursOnPayments < 0) {
            alert('Please enter valid positive numbers');
            return false;
        }

        // Validate conversion rate is between 1-100
        if (conversionRate < 1 || conversionRate > 100) {
            alert('Conversion rate must be between 1 and 100');
            return false;
        }

        return true;
    }

    /**
     * Get all form data
     * @returns {object} - Form data object
     */
    function getFormData() {
        return {
            quotesPerWeek: parseInt(document.getElementById('quotesPerWeek').value),
            minutesPerQuote: parseInt(document.getElementById('minutesPerQuote').value),
            avgJobValue: parseInt(document.getElementById('avgJobValue').value),
            conversionRate: parseInt(document.getElementById('conversionRate').value),
            hourlyRate: parseInt(document.getElementById('hourlyRate').value),
            paymentDelay: parseInt(document.querySelector('input[name="paymentDelay"]:checked').value),
            hoursOnPayments: parseInt(document.getElementById('hoursOnPayments').value)
        };
    }

    /**
     * Calculate ROI based on form data
     * @param {object} data - Form data
     * @returns {object} - Calculation results
     */
    function calculateROI(data) {
        // CALCULATION 1: Time Wasted on Manual Quoting
        const hoursPerWeekQuoting = (data.quotesPerWeek * data.minutesPerQuote) / 60;
        const hoursPerYearQuoting = hoursPerWeekQuoting * 52;
        const costOfQuotingTime = Math.round(hoursPerYearQuoting * data.hourlyRate);

        console.log('Quoting calculations:', {
            hoursPerWeekQuoting,
            hoursPerYearQuoting,
            costOfQuotingTime
        });

        // CALCULATION 2: Lost Revenue from Slow Follow-Up
        // Industry standard: Manual processes reduce conversion by 15%
        const potentialJobsPerYear = data.quotesPerWeek * 52 * (data.conversionRate / 100);
        const lostJobs = Math.round(potentialJobsPerYear * 0.15);
        const lostRevenue = Math.round(lostJobs * data.avgJobValue);

        console.log('Revenue calculations:', {
            potentialJobsPerYear,
            lostJobs,
            lostRevenue
        });

        // CALCULATION 3: Time Wasted on Payment Collection
        const paymentHoursPerYear = data.hoursOnPayments * 52;
        const costOfPaymentTime = Math.round(paymentHoursPerYear * data.hourlyRate);

        console.log('Payment calculations:', {
            paymentHoursPerYear,
            costOfPaymentTime
        });

        // TOTALS
        const totalAnnualCost = costOfQuotingTime + lostRevenue + costOfPaymentTime;
        const quoteIQAnnualCost = 188 * 12; // $2,256
        const netSavings = totalAnnualCost - quoteIQAnnualCost;
        const roi = Math.round((netSavings / quoteIQAnnualCost) * 100);

        console.log('Total calculations:', {
            totalAnnualCost,
            quoteIQAnnualCost,
            netSavings,
            roi
        });

        // WITH QUOTEIQ IMPROVEMENTS
        const newQuoteTime = 3; // minutes with QuoteIQ
        const newHoursPerWeekQuoting = (data.quotesPerWeek * newQuoteTime) / 60;
        const timeSavedPerWeek = hoursPerWeekQuoting - newHoursPerWeekQuoting;
        const improvedConversionRate = data.conversionRate + 12.5; // 10-15% boost, use 12.5% average

        console.log('QuoteIQ improvements:', {
            newQuoteTime,
            newHoursPerWeekQuoting,
            timeSavedPerWeek,
            improvedConversionRate
        });

        // Return all results
        return {
            // Breakdown 1: Quoting
            hoursPerWeekQuoting: hoursPerWeekQuoting.toFixed(1),
            hoursPerYearQuoting: Math.round(hoursPerYearQuoting),
            costOfQuotingTime: costOfQuotingTime,

            // Breakdown 2: Revenue
            lostJobs: lostJobs,
            lostRevenue: lostRevenue,

            // Breakdown 3: Payments
            paymentHoursPerYear: paymentHoursPerYear,
            costOfPaymentTime: costOfPaymentTime,

            // Totals
            totalAnnualCost: totalAnnualCost,
            quoteIQAnnualCost: quoteIQAnnualCost,
            netSavings: netSavings,
            roi: roi,

            // With QuoteIQ
            newQuoteTime: newQuoteTime,
            timeSavedPerWeek: timeSavedPerWeek.toFixed(1),
            improvedConversionRate: improvedConversionRate.toFixed(1)
        };
    }

    /**
     * Display results in the results section
     * @param {object} results - Calculation results
     */
    function displayResults(results) {
        console.log('Displaying results');

        // Top Summary Cards
        animateValue(document.getElementById('timeSavedPerWeek'), 0, parseFloat(results.timeSavedPerWeek), 1000, 1);
        animateValue(document.getElementById('netSavings'), 0, results.netSavings, 1000, 0, true);
        animateValue(document.getElementById('roiPercentage'), 0, results.roi, 1000, 0, false, '%');

        // Breakdown 1: Quoting
        animateValue(document.getElementById('hoursPerWeekQuoting'), 0, parseFloat(results.hoursPerWeekQuoting), 1000, 1);
        animateValue(document.getElementById('hoursPerYearQuoting'), 0, results.hoursPerYearQuoting, 1000, 0);
        animateValue(document.getElementById('costOfQuotingTime'), 0, results.costOfQuotingTime, 1000, 0, true);

        // Breakdown 2: Revenue
        animateValue(document.getElementById('lostJobs'), 0, results.lostJobs, 1000, 0);
        animateValue(document.getElementById('lostRevenue'), 0, results.lostRevenue, 1000, 0, true);

        // Breakdown 3: Payments
        animateValue(document.getElementById('paymentHoursPerYear'), 0, results.paymentHoursPerYear, 1000, 0);
        animateValue(document.getElementById('costOfPaymentTime'), 0, results.costOfPaymentTime, 1000, 0, true);

        // Investment Comparison
        animateValue(document.getElementById('totalAnnualCost'), 0, results.totalAnnualCost, 1000, 0, true);
        animateValue(document.getElementById('quoteIQAnnualCost'), 0, results.quoteIQAnnualCost, 1000, 0, true);
        animateValue(document.getElementById('netSavingsBottom'), 0, results.netSavings, 1000, 0, true);

        // With QuoteIQ improvements
        document.getElementById('newQuoteTime').textContent = results.newQuoteTime;
        document.getElementById('improvedConversionRate').textContent = results.improvedConversionRate + '%';
    }

    /**
     * Format number as currency
     * @param {number} number - Number to format
     * @returns {string} - Formatted currency string
     */
    function formatCurrency(number) {
        return '$' + number.toLocaleString('en-US');
    }

    /**
     * Animate number from start to end
     * @param {HTMLElement} element - Element to animate
     * @param {number} start - Start value
     * @param {number} end - End value
     * @param {number} duration - Animation duration in milliseconds
     * @param {number} decimals - Number of decimal places
     * @param {boolean} currency - Format as currency
     * @param {string} suffix - Suffix to add (e.g., '%')
     */
    function animateValue(element, start, end, duration, decimals = 0, currency = false, suffix = '') {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = progress * (end - start) + start;

            let displayValue;
            if (decimals > 0) {
                displayValue = current.toFixed(decimals);
            } else {
                displayValue = Math.floor(current);
            }

            if (currency) {
                element.textContent = formatCurrency(displayValue);
            } else {
                element.textContent = displayValue.toLocaleString('en-US') + suffix;
            }

            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    /**
     * Smooth scroll to element
     * @param {HTMLElement} element - Element to scroll to
     * @param {number} offset - Offset from top in pixels
     */
    function smoothScrollTo(element, offset = 100) {
        const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
        const offsetPosition = elementPosition - offset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
});
