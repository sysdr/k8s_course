import React, { useState } from 'react';
import { Button, TextField, MenuItem, Box, Alert } from '@mui/material';
import { submitLog } from '../services/api';

const LOG_LEVELS = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'];

function LogSubmitForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    level: 'INFO',
    message: '',
    service: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);

    try {
      await submitLog(formData);
      setResult({ type: 'success', message: 'Log submitted successfully' });
      setFormData({ level: 'INFO', message: '', service: '' });
      if (onSubmit) onSubmit();
    } catch (error) {
      setResult({ type: 'error', message: error.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextField
        select
        fullWidth
        label="Log Level"
        value={formData.level}
        onChange={(e) => setFormData({ ...formData, level: e.target.value })}
        margin="normal"
      >
        {LOG_LEVELS.map((level) => (
          <MenuItem key={level} value={level}>
            {level}
          </MenuItem>
        ))}
      </TextField>

      <TextField
        fullWidth
        label="Service Name"
        value={formData.service}
        onChange={(e) => setFormData({ ...formData, service: e.target.value })}
        margin="normal"
        required
      />

      <TextField
        fullWidth
        label="Log Message"
        value={formData.message}
        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
        margin="normal"
        multiline
        rows={3}
        required
      />

      <Button
        type="submit"
        variant="contained"
        color="primary"
        disabled={submitting}
        sx={{ mt: 2 }}
      >
        {submitting ? 'Submitting...' : 'Submit Log'}
      </Button>

      {result && (
        <Alert severity={result.type} sx={{ mt: 2 }}>
          {result.message}
        </Alert>
      )}
    </Box>
  );
}

export default LogSubmitForm;
