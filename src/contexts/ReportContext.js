import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

const ReportContext = createContext();

export const useReports = () => {
  const context = useContext(ReportContext);
  if (!context) {
    throw new Error('useReports must be used within a ReportProvider');
  }
  return context;
};

export const ReportProvider = ({ children }) => {
  const [reports, setReports] = useState([]);
  const [currentReport, setCurrentReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load reports from localStorage on mount
  useEffect(() => {
    const loadReports = () => {
      try {
        const savedReports = localStorage.getItem('reports');
        if (savedReports) {
          setReports(JSON.parse(savedReports));
        }
      } catch (error) {
        console.error('Error loading reports:', error);
        setError('Erreur lors du chargement des rapports');
      }
    };

    loadReports();
  }, []);

  // Save reports to localStorage when they change
  useEffect(() => {
    if (reports.length > 0) {
      localStorage.setItem('reports', JSON.stringify(reports));
    }
  }, [reports]);

  // Create a new report
  const createReport = useCallback((reportData) => {
    const newReport = {
      id: uuidv4(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'draft',
      ...reportData,
    };

    setReports(prev => [newReport, ...prev]);
    setCurrentReport(newReport);
    return newReport;
  }, []);

  // Update an existing report
  const updateReport = useCallback((reportId, updates) => {
    setReports(prev => 
      prev.map(report => 
        report.id === reportId 
          ? { ...report, ...updates, updatedAt: new Date().toISOString() }
          : report
      )
    );

    if (currentReport?.id === reportId) {
      setCurrentReport(prev => ({ ...prev, ...updates, updatedAt: new Date().toISOString() }));
    }

    return true;
  }, [currentReport]);

  // Delete a report
  const deleteReport = useCallback((reportId) => {
    setReports(prev => prev.filter(report => report.id !== reportId));
    
    if (currentReport?.id === reportId) {
      setCurrentReport(null);
    }

    return true;
  }, [currentReport]);

  // Get a report by ID
  const getReportById = useCallback((reportId) => {
    return reports.find(report => report.id === reportId);
  }, [reports]);

  // Get reports by type
  const getReportsByType = useCallback((reportType) => {
    return reports.filter(report => report.type === reportType);
  }, [reports]);

  // Get recent reports
  const getRecentReports = useCallback((limit = 10) => {
    return reports
      .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
      .slice(0, limit);
  }, [reports]);

  // Search reports
  const searchReports = useCallback((query) => {
    const lowercaseQuery = query.toLowerCase();
    return reports.filter(report => {
      const searchableFields = [
        report.patientName,
        report.patientId,
        report.indication,
        report.conclusion,
        report.type,
      ].filter(Boolean).join(' ').toLowerCase();
      
      return searchableFields.includes(lowercaseQuery);
    });
  }, [reports]);

  // Export report as JSON
  const exportReportAsJSON = useCallback((reportId) => {
    const report = getReportById(reportId);
    if (!report) return null;

    const dataStr = JSON.stringify(report, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `report-${report.patientName || report.id}-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    return true;
  }, [getReportById]);

  // Import reports from JSON
  const importReportsFromJSON = useCallback(async (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const importedData = JSON.parse(e.target.result);
          const importedReports = Array.isArray(importedData) ? importedData : [importedData];
          
          // Add new IDs to avoid conflicts
          const processedReports = importedReports.map(report => ({
            ...report,
            id: uuidv4(),
            importedAt: new Date().toISOString(),
            originalId: report.id,
          }));
          
          setReports(prev => [...processedReports, ...prev]);
          resolve(processedReports);
        } catch (error) {
          reject(new Error('Format de fichier invalide'));
        }
      };
      
      reader.onerror = () => reject(new Error('Erreur lors de la lecture du fichier'));
      reader.readAsText(file);
    });
  }, []);

  // Get statistics
  const getStatistics = useCallback(() => {
    const stats = {
      total: reports.length,
      byType: {},
      byStatus: {},
      lastWeek: 0,
      lastMonth: 0,
    };

    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    reports.forEach(report => {
      // By type
      stats.byType[report.type] = (stats.byType[report.type] || 0) + 1;
      
      // By status
      stats.byStatus[report.status] = (stats.byStatus[report.status] || 0) + 1;
      
      // Time-based
      const createdDate = new Date(report.createdAt);
      if (createdDate > weekAgo) stats.lastWeek++;
      if (createdDate > monthAgo) stats.lastMonth++;
    });

    return stats;
  }, [reports]);

  const value = {
    reports,
    currentReport,
    loading,
    error,
    createReport,
    updateReport,
    deleteReport,
    getReportById,
    getReportsByType,
    getRecentReports,
    searchReports,
    setCurrentReport,
    exportReportAsJSON,
    importReportsFromJSON,
    getStatistics,
  };

  return <ReportContext.Provider value={value}>{children}</ReportContext.Provider>;
};