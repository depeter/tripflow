import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { format } from 'date-fns';

/**
 * PDF Generation Service for TripFlow
 * Creates beautiful trip itinerary PDFs
 */

const COLORS = {
  primary: [16, 185, 129], // Green
  secondary: [59, 130, 246], // Blue
  dark: [31, 41, 55], // Gray-900
  light: [156, 163, 175], // Gray-400
  background: [249, 250, 251] // Gray-50
};

/**
 * Generate trip itinerary PDF
 * @param {Object} tripData - Trip data from context
 * @param {string} tripName - Name of the trip
 * @param {string} startDate - Trip start date
 */
export const generateTripPDF = (tripData, tripName = 'My Trip', startDate = null) => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.width;
  const pageHeight = doc.internal.pageSize.height;
  let yPos = 20;

  // Helper function to add new page if needed
  const checkNewPage = (requiredSpace = 20) => {
    if (yPos + requiredSpace > pageHeight - 20) {
      doc.addPage();
      yPos = 20;
      return true;
    }
    return false;
  };

  // Header - Gradient background
  doc.setFillColor(...COLORS.primary);
  doc.rect(0, 0, pageWidth, 50, 'F');

  // Trip Icon and Title
  doc.setFontSize(28);
  doc.setTextColor(255, 255, 255);
  doc.text('🗺️ ' + tripName, pageWidth / 2, 25, { align: 'center' });

  doc.setFontSize(11);
  doc.setTextColor(255, 255, 255);
  const subtitle = tripData.trip_type === 'multi_day'
    ? `${tripData.duration_days} Day Trip`
    : `${tripData.duration_hours} Hour Day Trip`;
  doc.text(subtitle, pageWidth / 2, 38, { align: 'center' });

  yPos = 60;

  // Trip Overview Section
  doc.setFillColor(...COLORS.background);
  doc.rect(10, yPos, pageWidth - 20, 45, 'F');

  doc.setFontSize(14);
  doc.setTextColor(...COLORS.primary);
  doc.setFont('helvetica', 'bold');
  doc.text('Trip Overview', 15, yPos + 8);

  doc.setFontSize(10);
  doc.setTextColor(...COLORS.dark);
  doc.setFont('helvetica', 'normal');

  const overviewData = [
    ['Start Location:', tripData.start_address || 'Not specified'],
    ['Trip Type:', tripData.is_round_trip ? 'Round Trip' : 'One Way'],
    ['Duration:', tripData.trip_type === 'multi_day'
      ? `${tripData.duration_days} days`
      : `${tripData.duration_hours} hours`],
    ['Max Distance:', `${tripData.max_distance_km || 500} km`],
  ];

  if (startDate) {
    overviewData.push(['Start Date:', format(new Date(startDate), 'MMMM d, yyyy')]);
  }

  if (tripData.route_stats) {
    overviewData.push(
      ['Total Distance:', `${tripData.route_stats.total_distance_km || 0} km`],
      ['Driving Time:', `${tripData.route_stats.estimated_driving_hours || 0} hours`]
    );
  }

  let tempY = yPos + 12;
  overviewData.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(label, 20, tempY);
    doc.setFont('helvetica', 'normal');
    doc.text(value, 70, tempY);
    tempY += 6;
  });

  yPos = tempY + 10;

  // Waypoints Section
  checkNewPage(20);
  doc.setFontSize(14);
  doc.setTextColor(...COLORS.primary);
  doc.setFont('helvetica', 'bold');
  doc.text('🎯 Itinerary', 15, yPos);
  yPos += 10;

  const waypoints = tripData.selected_waypoints || [];

  if (waypoints.length === 0) {
    doc.setFontSize(10);
    doc.setTextColor(...COLORS.light);
    doc.setFont('helvetica', 'italic');
    doc.text('No waypoints selected', 20, yPos);
    yPos += 10;
  } else {
    // Start location
    doc.setFillColor(240, 253, 244);
    doc.roundedRect(15, yPos, pageWidth - 30, 12, 3, 3, 'F');

    doc.setFontSize(11);
    doc.setTextColor(...COLORS.primary);
    doc.setFont('helvetica', 'bold');
    doc.text('📍 START', 20, yPos + 8);

    doc.setTextColor(...COLORS.dark);
    doc.setFont('helvetica', 'normal');
    doc.text(tripData.start_address || 'Start Location', 50, yPos + 8);
    yPos += 18;

    // Waypoints
    waypoints.forEach((waypoint, index) => {
      checkNewPage(25);

      // Waypoint box
      doc.setFillColor(255, 255, 255);
      doc.setDrawColor(...COLORS.light);
      doc.roundedRect(15, yPos, pageWidth - 30, 20, 3, 3, 'FD');

      // Waypoint number
      doc.setFillColor(...COLORS.secondary);
      doc.circle(25, yPos + 10, 5, 'F');
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.text(String(index + 1), 25, yPos + 11.5, { align: 'center' });

      // Waypoint name
      doc.setTextColor(...COLORS.dark);
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.text(waypoint.name || 'Location', 35, yPos + 8);

      // Waypoint details
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...COLORS.light);

      let details = [];
      if (waypoint.type) details.push(waypoint.type);
      if (waypoint.rating) details.push(`⭐ ${waypoint.rating}`);
      if (waypoint.price_per_night > 0) details.push(`€${waypoint.price_per_night}/night`);

      if (details.length > 0) {
        doc.text(details.join(' • '), 35, yPos + 14);
      }

      yPos += 25;
    });

    // End location (if round trip)
    if (tripData.is_round_trip) {
      checkNewPage(12);
      doc.setFillColor(240, 253, 244);
      doc.roundedRect(15, yPos, pageWidth - 30, 12, 3, 3, 'F');

      doc.setFontSize(11);
      doc.setTextColor(...COLORS.primary);
      doc.setFont('helvetica', 'bold');
      doc.text('🔄 RETURN', 20, yPos + 8);

      doc.setTextColor(...COLORS.dark);
      doc.setFont('helvetica', 'normal');
      doc.text(`Back to ${tripData.start_address || 'Start Location'}`, 55, yPos + 8);
      yPos += 18;
    }
  }

  // Trip Summary Section
  if (waypoints.length > 0) {
    checkNewPage(40);

    doc.setFontSize(14);
    doc.setTextColor(...COLORS.primary);
    doc.setFont('helvetica', 'bold');
    doc.text('📊 Trip Summary', 15, yPos);
    yPos += 10;

    const summaryData = [
      ['Number of Stops', String(waypoints.length)],
      ['Total Distance', `${tripData.route_stats?.total_distance_km || 0} km`],
      ['Estimated Driving Time', `${tripData.route_stats?.estimated_driving_hours || 0} hours`],
    ];

    // Calculate total cost if available
    const totalCost = waypoints.reduce((sum, wp) => {
      return sum + (wp.price_per_night || 0);
    }, 0);

    if (totalCost > 0) {
      summaryData.push(['Estimated Cost', `€${totalCost}`]);
    }

    doc.autoTable({
      startY: yPos,
      head: [['Metric', 'Value']],
      body: summaryData,
      theme: 'striped',
      headStyles: {
        fillColor: COLORS.primary,
        fontSize: 10,
        fontStyle: 'bold'
      },
      bodyStyles: {
        fontSize: 10
      },
      alternateRowStyles: {
        fillColor: COLORS.background
      },
      margin: { left: 15, right: 15 }
    });

    yPos = doc.lastAutoTable.finalY + 10;
  }

  // Preferences Section (if available)
  if (tripData.interests && tripData.interests.length > 0) {
    checkNewPage(30);

    doc.setFontSize(14);
    doc.setTextColor(...COLORS.primary);
    doc.setFont('helvetica', 'bold');
    doc.text('🎨 Your Preferences', 15, yPos);
    yPos += 10;

    doc.setFontSize(10);
    doc.setTextColor(...COLORS.dark);
    doc.setFont('helvetica', 'normal');

    if (tripData.interests.length > 0) {
      doc.setFont('helvetica', 'bold');
      doc.text('Interests:', 20, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(tripData.interests.join(', '), 50, yPos);
      yPos += 6;
    }

    if (tripData.preferred_environment && tripData.preferred_environment.length > 0) {
      doc.setFont('helvetica', 'bold');
      doc.text('Environment:', 20, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(tripData.preferred_environment.join(', '), 50, yPos);
      yPos += 6;
    }

    if (tripData.activity_level) {
      doc.setFont('helvetica', 'bold');
      doc.text('Activity Level:', 20, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(tripData.activity_level, 50, yPos);
      yPos += 6;
    }
  }

  // Footer
  const footerY = pageHeight - 15;
  doc.setFontSize(8);
  doc.setTextColor(...COLORS.light);
  doc.setFont('helvetica', 'italic');
  doc.text('Generated by TripFlow - Your AI Travel Companion', pageWidth / 2, footerY, { align: 'center' });
  doc.text(`Generated on ${format(new Date(), 'MMMM d, yyyy')}`, pageWidth / 2, footerY + 4, { align: 'center' });

  // Save the PDF
  const fileName = `${tripName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_itinerary.pdf`;
  doc.save(fileName);
};

/**
 * Generate a quick summary PDF (single page)
 */
export const generateQuickSummaryPDF = (tripData, tripName = 'My Trip') => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.width;

  // Header
  doc.setFillColor(...COLORS.primary);
  doc.rect(0, 0, pageWidth, 40, 'F');

  doc.setFontSize(24);
  doc.setTextColor(255, 255, 255);
  doc.text('🗺️ ' + tripName, pageWidth / 2, 25, { align: 'center' });

  let yPos = 50;

  // Quick stats
  const waypoints = tripData.selected_waypoints || [];
  const stats = [
    ['Stops:', String(waypoints.length)],
    ['Distance:', `${tripData.route_stats?.total_distance_km || 0} km`],
    ['Duration:', tripData.trip_type === 'multi_day'
      ? `${tripData.duration_days} days`
      : `${tripData.duration_hours} hours`]
  ];

  doc.setFontSize(12);
  doc.setTextColor(...COLORS.dark);
  stats.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(label, 20, yPos);
    doc.setFont('helvetica', 'normal');
    doc.text(value, 60, yPos);
    yPos += 8;
  });

  yPos += 10;

  // Waypoints list
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('Locations:', 20, yPos);
  yPos += 8;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');

  waypoints.forEach((wp, idx) => {
    doc.text(`${idx + 1}. ${wp.name}`, 25, yPos);
    yPos += 6;
  });

  const fileName = `${tripName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_summary.pdf`;
  doc.save(fileName);
};

export default {
  generateTripPDF,
  generateQuickSummaryPDF
};
