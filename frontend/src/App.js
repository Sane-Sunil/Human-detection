import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
} from '@mui/material';
import axios from 'axios';
import ReactPlayer from 'react-player';

// Use environment variable for API URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Configure axios defaults
axios.defaults.baseURL = API_URL;
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.withCredentials = true;

// Add error interceptor
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      console.error('Error response:', error.response.data);
      console.error('Error status:', error.response.status);
    } else if (error.request) {
      console.error('Error request:', error.request);
    } else {
      console.error('Error message:', error.message);
    }
    return Promise.reject(error);
  }
);

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [videos, setVideos] = useState([]);
  const [detections, setDetections] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingVideo, setProcessingVideo] = useState(false);
  const [videoStatus, setVideoStatus] = useState(null);
  const [error, setError] = useState(null);

  // Add polling interval state
  const [pollInterval, setPollInterval] = useState(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, []);

  useEffect(() => {
    fetchVideos();
  }, []);

  const checkVideoStatus = async (videoId) => {
    try {
      const response = await axios.get(`/video/${videoId}/status`);
      setVideoStatus(response.data);
      
      // If processing is complete (progress is 100%), stop polling and fetch detections
      if (response.data.progress >= 100) {
        if (pollInterval) {
          clearInterval(pollInterval);
          setPollInterval(null);
        }
        setProcessingVideo(false);
        await fetchDetections(videoId);
      } else if (response.data.progress === -1) {
        // If progress is -1, there was an error
        setError('Failed to process video. Please try again.');
        if (pollInterval) {
          clearInterval(pollInterval);
          setPollInterval(null);
        }
        setProcessingVideo(false);
      } else if (response.data.progress === 0) {
        // If progress is still 0 after a while, there might be an issue
        if (videoStatus && videoStatus.progress === 0) {
          setError('Video processing seems to be stuck. Please try uploading the video again.');
          if (pollInterval) {
            clearInterval(pollInterval);
            setPollInterval(null);
          }
          setProcessingVideo(false);
        }
      }
    } catch (error) {
      console.error('Error checking video status:', error);
      setError('Failed to check video status. Please try again.');
      if (pollInterval) {
        clearInterval(pollInterval);
        setPollInterval(null);
      }
      setProcessingVideo(false);
    }
  };

  const fetchVideos = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/videos');
      setVideos(response.data);
    } catch (error) {
      console.error('Error fetching videos:', error);
      setError('Failed to fetch videos. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchDetections = async (videoId) => {
    try {
      const response = await axios.get(`/detections/${videoId}`);
      setDetections(response.data);
    } catch (error) {
      console.error('Error fetching detections:', error);
      setError('Failed to fetch detections. Please try again.');
    }
  };

  const handleFileSelect = (event) => {
    setSelectedFile(event.target.files[0]);
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post('/video/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Start polling for status
      const interval = setInterval(() => {
        checkVideoStatus(response.data.id);
      }, 2000);
      setPollInterval(interval);
      setProcessingVideo(true);

      // Refresh videos list
      await fetchVideos();
    } catch (error) {
      console.error('Error uploading video:', error);
      setError('Failed to upload video. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewVideo = async (video) => {
    try {
      setLoading(true);
      setError(null);
      setSelectedVideo(video);
      await fetchDetections(video.id);
    } catch (error) {
      console.error('Error viewing video:', error);
      setError('Failed to load video. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteVideo = async (videoId, e) => {
    e.stopPropagation();
    try {
      setLoading(true);
      setError(null);
      await axios.delete(`/video/${videoId}`);
      await fetchVideos();
      if (selectedVideo && selectedVideo.id === videoId) {
        setSelectedVideo(null);
        setDetections([]);
      }
    } catch (error) {
      console.error('Error deleting video:', error);
      setError('Failed to delete video. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Video Processing Dashboard
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Paper sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <input
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              id="video-upload"
            />
            <label htmlFor="video-upload">
              <Button variant="contained" component="span">
                Select Video
              </Button>
            </label>
            {selectedFile && (
              <Typography>{selectedFile.name}</Typography>
            )}
            <Button
              variant="contained"
              color="primary"
              onClick={handleUpload}
              disabled={!selectedFile || loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Upload'}
            </Button>
          </Box>
        </Paper>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Paper sx={{ p: 2, flex: 1 }}>
            <Typography variant="h6" gutterBottom>
              Video List
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Filename</TableCell>
                    <TableCell>Upload Date</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {videos.map((video) => (
                    <TableRow
                      key={video.id}
                      onClick={() => handleViewVideo(video)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>{video.filename}</TableCell>
                      <TableCell>
                        {new Date(video.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewVideo(video);
                          }}
                        >
                          View
                        </Button>
                        <Button
                          variant="outlined"
                          color="error"
                          size="small"
                          onClick={(e) => handleDeleteVideo(video.id, e)}
                          sx={{ ml: 1 }}
                        >
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Paper sx={{ p: 2, flex: 1 }}>
            {selectedVideo ? (
              <>
                <Typography variant="h6" gutterBottom>
                  Video Preview
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <ReactPlayer
                    url={`${API_URL}/video/${selectedVideo.id}/processed`}
                    controls
                    width="100%"
                    height="auto"
                    config={{
                      file: {
                        attributes: {
                          controlsList: 'nodownload',
                          disablePictureInPicture: true,
                        },
                        forceHLS: false,
                        hlsOptions: {
                          enableLowLatencyMode: true,
                        },
                      },
                    }}
                    onError={(e) => {
                      console.error('Video player error:', e);
                      setError('Failed to load processed video. Please try again.');
                    }}
                  />
                </Box>
                <Typography variant="h6" gutterBottom>
                  Detection Results
                </Typography>
                {processingVideo ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 2 }}>
                    <CircularProgress 
                      variant="determinate" 
                      value={videoStatus?.progress || 0} 
                      sx={{ mb: 2 }} 
                    />
                    <Typography color="text.secondary">
                      {videoStatus ? (
                        `Processing video... ${videoStatus.progress?.toFixed(1) || 0}% complete`
                      ) : (
                        'Initializing video processing...'
                      )}
                    </Typography>
                    {videoStatus && videoStatus.detections_count > 0 && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Detections found: {videoStatus.detections_count}
                      </Typography>
                    )}
                  </Box>
                ) : detections.length === 0 ? (
                  <Typography color="text.secondary">
                    No detections found. The video might still be processing or no people were detected.
                  </Typography>
                ) : (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Frame</TableCell>
                          <TableCell>Confidence</TableCell>
                          <TableCell>Timestamp</TableCell>
                          <TableCell>Position</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {detections.map((detection) => (
                          <TableRow key={detection.id}>
                            <TableCell>{detection.frame_number}</TableCell>
                            <TableCell>
                              {(detection.confidence * 100).toFixed(2)}%
                            </TableCell>
                            <TableCell>
                              {new Date(detection.timestamp).toLocaleString()}
                            </TableCell>
                            <TableCell>
                              x: {detection.x.toFixed(2)}, y: {detection.y.toFixed(2)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </>
            ) : (
              <Typography>Select a video to view details</Typography>
            )}
          </Paper>
        </Box>
      </Box>
    </Container>
  );
}

export default App; 