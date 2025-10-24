// TestsPanel.jsx
import React, { useState, useEffect } from 'react';
import { requirementsAPI } from '../../services/api';

const TestsPanel = ({ projectStatus }) => {
  const [testCases, setTestCases] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [expandedRequirements, setExpandedRequirements] = useState(new Set());
  const [editingTestCase, setEditingTestCase] = useState(null);

  // Load test cases when project status changes
  useEffect(() => {
    if (projectStatus?.thread_id && projectStatus?.requirements) {
      loadAllTestCases();
    }
  }, [projectStatus?.thread_id, projectStatus?.requirements]);

  const loadAllTestCases = async () => {
    if (!projectStatus?.thread_id || !projectStatus?.requirements) return;

    setLoading(true);
    const testCasesData = {};
    try {
      for (let i = 0; i < projectStatus.requirements.length; i++) {
        const result = await requirementsAPI.getTestCases(projectStatus.thread_id, i);
        testCasesData[i] = result.test_cases || [];
      }
      setTestCases(testCasesData);
    } catch (error) {
      console.error('Error loading test cases:', error);
      setMessage('Error loading test cases');
    } finally {
      setLoading(false);
    }
  };

  const generateTestCases = async (reqIndex) => {
    if (!projectStatus?.thread_id) return;

    setLoading(true);
    setMessage('');
    try {
      await requirementsAPI.generateTestCases(projectStatus.thread_id, reqIndex);
      
      // Reload test cases for this requirement
      const result = await requirementsAPI.getTestCases(projectStatus.thread_id, reqIndex);
      setTestCases(prev => ({
        ...prev,
        [reqIndex]: result.test_cases || []
      }));
      
      // Expand the requirement to show generated tests
      setExpandedRequirements(prev => new Set(prev).add(reqIndex));
      setMessage(`✅ Generated test cases for requirement ${reqIndex + 1}`);
    } catch (error) {
      setMessage(`❌ Error generating test cases: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const saveTestCases = async (reqIndex) => {
    if (!projectStatus?.thread_id || !testCases[reqIndex]) return;

    setLoading(true);
    setMessage('');
    try {
      await requirementsAPI.saveTestCases(
        projectStatus.thread_id,
        reqIndex,
        testCases[reqIndex]
      );
      setMessage(`✅ Saved test cases for requirement ${reqIndex + 1} to Neo4j`);
    } catch (error) {
      setMessage(`❌ Error saving test cases: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const updateTestCase = (reqIndex, testIndex, field, value) => {
    setTestCases(prev => {
      const updated = { ...prev };
      if (updated[reqIndex] && updated[reqIndex][testIndex]) {
        updated[reqIndex][testIndex] = {
          ...updated[reqIndex][testIndex],
          [field]: value
        };
      }
      return updated;
    });
  };

  const addTestCase = (reqIndex) => {
    const newTestCase = {
      test_id: `TC_REQ${reqIndex + 1}_${String((testCases[reqIndex]?.length || 0) + 1).padStart(3, '0')}`,
      description: 'New test case description',
      test_steps: ['Step 1', 'Step 2'],
      expected_result: 'Expected outcome',
      test_type: 'Functional'
    };

    setTestCases(prev => ({
      ...prev,
      [reqIndex]: [...(prev[reqIndex] || []), newTestCase]
    }));
  };

  const removeTestCase = (reqIndex, testIndex) => {
    setTestCases(prev => {
      const updated = { ...prev };
      if (updated[reqIndex]) {
        updated[reqIndex] = updated[reqIndex].filter((_, idx) => idx !== testIndex);
        // Reindex test IDs
        updated[reqIndex] = updated[reqIndex].map((testCase, idx) => ({
          ...testCase,
          test_id: `TC_REQ${reqIndex + 1}_${String(idx + 1).padStart(3, '0')}`
        }));
      }
      return updated;
    });
  };

  const addTestStep = (reqIndex, testIndex) => {
    setTestCases(prev => {
      const updated = { ...prev };
      if (updated[reqIndex] && updated[reqIndex][testIndex]) {
        updated[reqIndex][testIndex].test_steps.push(`Step ${updated[reqIndex][testIndex].test_steps.length + 1}`);
      }
      return updated;
    });
  };

  const updateTestStep = (reqIndex, testIndex, stepIndex, value) => {
    setTestCases(prev => {
      const updated = { ...prev };
      if (updated[reqIndex] && updated[reqIndex][testIndex]) {
        const newSteps = [...updated[reqIndex][testIndex].test_steps];
        newSteps[stepIndex] = value;
        updated[reqIndex][testIndex].test_steps = newSteps;
      }
      return updated;
    });
  };

  const removeTestStep = (reqIndex, testIndex, stepIndex) => {
    setTestCases(prev => {
      const updated = { ...prev };
      if (updated[reqIndex] && updated[reqIndex][testIndex]) {
        updated[reqIndex][testIndex].test_steps = 
          updated[reqIndex][testIndex].test_steps.filter((_, idx) => idx !== stepIndex);
      }
      return updated;
    });
  };

  const toggleRequirementExpansion = (reqIndex) => {
    setExpandedRequirements(prev => {
      const newSet = new Set(prev);
      if (newSet.has(reqIndex)) {
        newSet.delete(reqIndex);
      } else {
        newSet.add(reqIndex);
      }
      return newSet;
    });
  };

  const getTestCasesCount = (reqIndex) => {
    return testCases[reqIndex] ? testCases[reqIndex].length : 0;
  };

  const generateAllTestCases = async () => {
    if (!projectStatus?.thread_id || !projectStatus?.requirements) return;

    setLoading(true);
    setMessage('Generating test cases for all requirements...');
    
    try {
      for (let i = 0; i < projectStatus.requirements.length; i++) {
        await requirementsAPI.generateTestCases(projectStatus.thread_id, i);
        // Reload test cases for this requirement
        const result = await requirementsAPI.getTestCases(projectStatus.thread_id, i);
        setTestCases(prev => ({
          ...prev,
          [i]: result.test_cases || []
        }));
      }
      
      // Expand all requirements
      const allIndices = new Set(projectStatus.requirements.map((_, index) => index));
      setExpandedRequirements(allIndices);
      setMessage('✅ Generated test cases for all requirements');
    } catch (error) {
      setMessage(`❌ Error generating test cases: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!projectStatus?.requirements) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2>Test Case Management</h2>
          <p>Generate and manage test cases for requirements</p>
        </div>
        <div className="card">
          <div className="text-gray text-center py-8">
            Please create a project and generate requirements first.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Test Case Management</h2>
        <p>Generate and manage test cases for requirements</p>
      </div>

      {message && (
        <div className={`alert ${message.includes('❌') ? 'alert-error' : 'alert-success'}`}>
          {message}
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <div className="card-title">Test Cases Overview</div>
          <div className="flex gap-4">
            <button
              className="btn btn-secondary"
              onClick={loadAllTestCases}
              disabled={loading}
            >
              {loading && <span className="spinner"></span>}
              Refresh Tests
            </button>
            <button
              className="btn btn-primary"
              onClick={generateAllTestCases}
              disabled={loading}
            >
              {loading && <span className="spinner"></span>}
              Generate All Tests
            </button>
          </div>
        </div>

        <div className="p-4">
          <div className="requirements-list">
            {projectStatus.requirements.map((requirement, index) => (
              <div key={index} className="requirement-card">
                <div className="requirement-card-header">
                  <div className="requirement-info">
                    <h3 className="requirement-title">Requirement {index + 1}</h3>
                    <p className="requirement-description">{requirement}</p>
                  </div>
                  
                  <div className="requirement-status">
                    <span className={`status-badge ${
                      getTestCasesCount(index) > 0 ? 'status-approved' : 'status-pending'
                    }`}>
                      {getTestCasesCount(index) > 0 ? 'Tested' : 'No Tests'}
                    </span>
                    <span className="test-count">{getTestCasesCount(index)} test cases</span>
                  </div>
                  
                  <div className="requirement-actions">
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => generateTestCases(index)}
                      disabled={loading}
                    >
                      Generate Tests
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => toggleRequirementExpansion(index)}
                    >
                      {expandedRequirements.has(index) ? 'Hide' : 'Show'} Tests
                    </button>
                  </div>
                </div>

                {/* Test Cases Section */}
                {expandedRequirements.has(index) && (
                  <div className="test-cases-section">
                    {testCases[index] && testCases[index].length > 0 ? (
                      <div className="test-cases-content">
                        <div className="test-cases-header">
                          <h4>Test Cases ({testCases[index].length})</h4>
                          <div className="test-cases-actions">
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => addTestCase(index)}
                            >
                              + Add Test Case
                            </button>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => saveTestCases(index)}
                              disabled={loading}
                            >
                              {loading && <span className="spinner"></span>}
                              Save to Neo4j
                            </button>
                          </div>
                        </div>

                        {/* Test Cases Cards */}
                        <div className="test-cases-grid">
                          {testCases[index].map((testCase, testIndex) => (
                            <div key={testIndex} className="test-case-card">
                              <div className="test-case-header">
                                <div className="test-case-id">{testCase.test_id}</div>
                                <span className={`test-type-badge test-type-${testCase.test_type.toLowerCase()}`}>
                                  {testCase.test_type}
                                </span>
                              </div>
                              
                              <div className="test-case-content">
                                <div className="test-case-field">
                                  <label>Description:</label>
                                  {editingTestCase?.reqIndex === index && editingTestCase?.testIndex === testIndex ? (
                                    <textarea
                                      className="form-input textarea text-sm"
                                      value={testCase.description}
                                      onChange={(e) => updateTestCase(index, testIndex, 'description', e.target.value)}
                                      rows={2}
                                    />
                                  ) : (
                                    <div className="test-case-value">{testCase.description}</div>
                                  )}
                                </div>

                                <div className="test-case-field">
                                  <label>Test Steps:</label>
                                  {editingTestCase?.reqIndex === index && editingTestCase?.testIndex === testIndex ? (
                                    <div className="test-steps-editable">
                                      {testCase.test_steps.map((step, stepIndex) => (
                                        <div key={stepIndex} className="test-step-editable">
                                          <span className="step-number">{stepIndex + 1}.</span>
                                          <input
                                            type="text"
                                            className="form-input text-sm"
                                            value={step}
                                            onChange={(e) => updateTestStep(index, testIndex, stepIndex, e.target.value)}
                                          />
                                          <button
                                            className="btn-action btn-delete text-xs"
                                            onClick={() => removeTestStep(index, testIndex, stepIndex)}
                                          >
                                            ×
                                          </button>
                                        </div>
                                      ))}
                                      <button
                                        className="btn-action btn-edit text-xs"
                                        onClick={() => addTestStep(index, testIndex)}
                                      >
                                        + Add Step
                                      </button>
                                    </div>
                                  ) : (
                                    <div className="test-steps">
                                      <ol className="test-steps-list">
                                        {testCase.test_steps.map((step, stepIndex) => (
                                          <li key={stepIndex} className="test-step">
                                            {step}
                                          </li>
                                        ))}
                                      </ol>
                                    </div>
                                  )}
                                </div>

                                <div className="test-case-field">
                                  <label>Expected Result:</label>
                                  {editingTestCase?.reqIndex === index && editingTestCase?.testIndex === testIndex ? (
                                    <textarea
                                      className="form-input textarea text-sm"
                                      value={testCase.expected_result}
                                      onChange={(e) => updateTestCase(index, testIndex, 'expected_result', e.target.value)}
                                      rows={2}
                                    />
                                  ) : (
                                    <div className="test-case-value">{testCase.expected_result}</div>
                                  )}
                                </div>

                                <div className="test-case-actions">
                                  {editingTestCase?.reqIndex === index && editingTestCase?.testIndex === testIndex ? (
                                    <>
                                      <button
                                        className="btn-action btn-update"
                                        onClick={() => setEditingTestCase(null)}
                                      >
                                        ✓ Save
                                      </button>
                                      <button
                                        className="btn-action btn-delete"
                                        onClick={() => setEditingTestCase(null)}
                                      >
                                        ✗ Cancel
                                      </button>
                                    </>
                                  ) : (
                                    <>
                                      <button
                                        className="btn-action btn-edit"
                                        onClick={() => setEditingTestCase({ reqIndex: index, testIndex })}
                                      >
                                        ✏️ Edit
                                      </button>
                                      <button
                                        className="btn-action btn-delete"
                                        onClick={() => removeTestCase(index, testIndex)}
                                      >
                                        🗑️ Delete
                                      </button>
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="no-test-cases">
                        <div className="text-gray-500 mb-4">No test cases generated yet</div>
                        <button
                          className="btn btn-primary"
                          onClick={() => generateTestCases(index)}
                          disabled={loading}
                        >
                          {loading && <span className="spinner"></span>}
                          Generate Test Cases
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="card-footer">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray">
              Total Requirements: <strong>{projectStatus.requirements.length}</strong> | 
              Requirements with Tests: <strong>{Object.values(testCases).filter(tc => tc && tc.length > 0).length}</strong> |
              Total Test Cases: <strong>{Object.values(testCases).reduce((sum, tc) => sum + (tc ? tc.length : 0), 0)}</strong>
            </div>
            <div className="text-sm text-gray">
              Project: <strong>{projectStatus.thread_id}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestsPanel;