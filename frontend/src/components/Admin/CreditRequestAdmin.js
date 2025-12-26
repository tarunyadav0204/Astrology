import React, { useState, useEffect } from 'react';
import './CreditRequestAdmin.css';

const CreditRequestAdmin = () => {
    const [pendingRequests, setPendingRequests] = useState([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    useEffect(() => {
        loadPendingRequests();
    }, []);

    const loadPendingRequests = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/credits/requests/pending');
            if (response.ok) {
                const data = await response.json();
                setPendingRequests(data.requests || []);
            }
        } catch (error) {
            console.error('Error loading requests:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (requestId, approvedAmount, adminNotes) => {
        try {
            const response = await fetch('/api/credits/requests/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    request_id: requestId,
                    approved_amount: parseInt(approvedAmount),
                    admin_notes: adminNotes
                })
            });

            const data = await response.json();
            if (data.success) {
                setMessage(`✅ ${data.message}`);
                loadPendingRequests();
            } else {
                setMessage(`❌ ${data.message}`);
            }
        } catch (error) {
            setMessage('❌ Error approving request');
        }
    };

    const handleReject = async (requestId, adminNotes) => {
        try {
            const response = await fetch('/api/credits/requests/reject', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    request_id: requestId,
                    admin_notes: adminNotes
                })
            });

            const data = await response.json();
            if (data.success) {
                setMessage(`✅ ${data.message}`);
                loadPendingRequests();
            } else {
                setMessage(`❌ ${data.message}`);
            }
        } catch (error) {
            setMessage('❌ Error rejecting request');
        }
    };

    const RequestItem = ({ request }) => {
        const [approvedAmount, setApprovedAmount] = useState(request.requested_amount);
        const [adminNotes, setAdminNotes] = useState('');
        const [processing, setProcessing] = useState(false);

        const onApprove = async () => {
            setProcessing(true);
            await handleApprove(request.id, approvedAmount, adminNotes);
            setProcessing(false);
        };

        const onReject = async () => {
            setProcessing(true);
            await handleReject(request.id, adminNotes);
            setProcessing(false);
        };

        return (
            <div className="request-admin-item">
                <div className="request-header">
                    <h4>{request.user_name}</h4>
                    <span className="request-id">ID: {request.id}</span>
                </div>
                
                <div className="request-details">
                    <p><strong>Requested:</strong> {request.requested_amount} credits</p>
                    <p><strong>Reason:</strong> {request.reason}</p>
                    <p><strong>Date:</strong> {new Date(request.created_at).toLocaleString()}</p>
                </div>

                <div className="admin-controls">
                    <div className="control-group">
                        <label>Approved Amount:</label>
                        <input
                            type="number"
                            value={approvedAmount}
                            onChange={(e) => setApprovedAmount(e.target.value)}
                            min="0"
                            max="100"
                            disabled={processing}
                        />
                    </div>
                    
                    <div className="control-group">
                        <label>Admin Notes:</label>
                        <textarea
                            value={adminNotes}
                            onChange={(e) => setAdminNotes(e.target.value)}
                            placeholder="Optional notes for the user"
                            rows="2"
                            disabled={processing}
                        />
                    </div>

                    <div className="action-buttons">
                        <button 
                            className="approve-btn"
                            onClick={onApprove}
                            disabled={processing}
                        >
                            {processing ? 'Processing...' : 'Approve'}
                        </button>
                        <button 
                            className="reject-btn"
                            onClick={onReject}
                            disabled={processing}
                        >
                            {processing ? 'Processing...' : 'Reject'}
                        </button>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="credit-request-admin">
            <div className="admin-header">
                <h2>📋 Credit Request Management</h2>
                <button onClick={loadPendingRequests} disabled={loading}>
                    {loading ? 'Loading...' : 'Refresh'}
                </button>
            </div>

            {message && (
                <div className={`admin-message ${message.includes('✅') ? 'success' : 'error'}`}>
                    {message}
                </div>
            )}

            <div className="requests-container">
                {pendingRequests.length === 0 ? (
                    <div className="no-requests">
                        {loading ? 'Loading requests...' : 'No pending credit requests'}
                    </div>
                ) : (
                    pendingRequests.map(request => (
                        <RequestItem key={request.id} request={request} />
                    ))
                )}
            </div>
        </div>
    );
};

export default CreditRequestAdmin;