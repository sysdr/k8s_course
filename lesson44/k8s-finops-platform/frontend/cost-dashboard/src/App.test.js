import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import axios from 'axios';
import App from './App';

jest.mock('axios');

test('renders FinOps dashboard title', async () => {
  axios.get.mockRejectedValue(new Error('no server'));
  render(<App />);
  const title = await screen.findByText(/Kubernetes FinOps Dashboard/i, {}, { timeout: 5000 });
  expect(title).toBeInTheDocument();
});
