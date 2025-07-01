import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  Avatar,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
} from '@mui/material';
import {
  Person,
  Settings,
  Security,
  Notifications,
  Save,
  Edit,
  Delete,
  Add,
} from '@mui/icons-material';
import { useUser } from '../contexts/UserContext';

const UserProfile = () => {
  const { currentUser, setCurrentUser } = useUser();
  const [activeTab, setActiveTab] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [formData, setFormData] = useState({
    name: currentUser?.name || '',
    email: currentUser?.email || '',
    specialty: currentUser?.specialty || '',
    hospital: currentUser?.hospital || '',
    phoneNumber: '',
    address: '',
    licenseNumber: '',
  });

  const [preferences, setPreferences] = useState({
    language: 'fr',
    autoSave: true,
    speechRecognitionEnabled: true,
    notificationEnabled: true,
    defaultExamType: 'scanner',
    pdfTemplate: 'standard',
  });

  const [customTemplates, setCustomTemplates] = useState([
    {
      id: '1',
      name: 'Template Scanner Personnel',
      type: 'scanner',
      description: 'Template personnalisé pour les scanners thoraciques'
    },
    {
      id: '2',
      name: 'Template IRM Urgence',
      type: 'mri',
      description: 'Template rapide pour les IRM d\'urgence'
    }
  ]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handlePreferenceChange = (field, value) => {
    setPreferences(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    // Update user data
    setCurrentUser(prev => ({
      ...prev,
      ...formData
    }));
    
    setIsEditing(false);
    setSaveMessage('Profil mis à jour avec succès');
    setTimeout(() => setSaveMessage(''), 3000);
  };

  const handleEditToggle = () => {
    if (isEditing) {
      // Reset form data if canceling
      setFormData({
        name: currentUser?.name || '',
        email: currentUser?.email || '',
        specialty: currentUser?.specialty || '',
        hospital: currentUser?.hospital || '',
        phoneNumber: '',
        address: '',
        licenseNumber: '',
      });
    }
    setIsEditing(!isEditing);
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`profile-tabpanel-${index}`}
      aria-labelledby={`profile-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Profil Utilisateur
      </Typography>

      {saveMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {saveMessage}
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="profile tabs"
        >
          <Tab label="Informations personnelles" icon={<Person />} />
          <Tab label="Préférences" icon={<Settings />} />
          <Tab label="Templates personnalisés" icon={<Edit />} />
          <Tab label="Sécurité" icon={<Security />} />
        </Tabs>

        {/* Personal Information Tab */}
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Avatar sx={{ width: 120, height: 120, mb: 2, fontSize: '2rem' }}>
                  {currentUser?.name?.charAt(0)}
                </Avatar>
                <Typography variant="h6">{currentUser?.name}</Typography>
                <Typography color="text.secondary">{currentUser?.specialty}</Typography>
                <Button
                  variant="outlined"
                  startIcon={<Edit />}
                  onClick={handleEditToggle}
                  sx={{ mt: 2 }}
                >
                  {isEditing ? 'Annuler' : 'Modifier'}
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={8}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Nom complet"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    disabled={!isEditing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    disabled={!isEditing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Spécialité"
                    value={formData.specialty}
                    onChange={(e) => handleInputChange('specialty', e.target.value)}
                    disabled={!isEditing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Établissement"
                    value={formData.hospital}
                    onChange={(e) => handleInputChange('hospital', e.target.value)}
                    disabled={!isEditing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Téléphone"
                    value={formData.phoneNumber}
                    onChange={(e) => handleInputChange('phoneNumber', e.target.value)}
                    disabled={!isEditing}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="N° de licence"
                    value={formData.licenseNumber}
                    onChange={(e) => handleInputChange('licenseNumber', e.target.value)}
                    disabled={!isEditing}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Adresse"
                    multiline
                    rows={2}
                    value={formData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    disabled={!isEditing}
                  />
                </Grid>
                {isEditing && (
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                      <Button
                        variant="outlined"
                        onClick={handleEditToggle}
                      >
                        Annuler
                      </Button>
                      <Button
                        variant="contained"
                        startIcon={<Save />}
                        onClick={handleSave}
                      >
                        Sauvegarder
                      </Button>
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Preferences Tab */}
        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Paramètres généraux
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>Langue</InputLabel>
                      <Select
                        value={preferences.language}
                        label="Langue"
                        onChange={(e) => handlePreferenceChange('language', e.target.value)}
                      >
                        <MenuItem value="fr">Français</MenuItem>
                        <MenuItem value="en">English</MenuItem>
                      </Select>
                    </FormControl>
                    
                    <FormControl fullWidth>
                      <InputLabel>Type d'examen par défaut</InputLabel>
                      <Select
                        value={preferences.defaultExamType}
                        label="Type d'examen par défaut"
                        onChange={(e) => handlePreferenceChange('defaultExamType', e.target.value)}
                      >
                        <MenuItem value="scanner">Scanner</MenuItem>
                        <MenuItem value="mri">IRM</MenuItem>
                        <MenuItem value="echo">Échographie</MenuItem>
                      </Select>
                    </FormControl>

                    <FormControl fullWidth>
                      <InputLabel>Template PDF</InputLabel>
                      <Select
                        value={preferences.pdfTemplate}
                        label="Template PDF"
                        onChange={(e) => handlePreferenceChange('pdfTemplate', e.target.value)}
                      >
                        <MenuItem value="standard">Standard</MenuItem>
                        <MenuItem value="detailed">Détaillé</MenuItem>
                        <MenuItem value="compact">Compact</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Fonctionnalités
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preferences.autoSave}
                          onChange={(e) => handlePreferenceChange('autoSave', e.target.checked)}
                        />
                      }
                      label="Sauvegarde automatique"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preferences.speechRecognitionEnabled}
                          onChange={(e) => handlePreferenceChange('speechRecognitionEnabled', e.target.checked)}
                        />
                      }
                      label="Reconnaissance vocale"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preferences.notificationEnabled}
                          onChange={(e) => handlePreferenceChange('notificationEnabled', e.target.checked)}
                        />
                      }
                      label="Notifications"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<Save />}
              onClick={() => {
                setSaveMessage('Préférences sauvegardées');
                setTimeout(() => setSaveMessage(''), 3000);
              }}
            >
              Sauvegarder les préférences
            </Button>
          </Box>
        </TabPanel>

        {/* Custom Templates Tab */}
        <TabPanel value={activeTab} index={2}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Templates personnalisés
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => {
                // In a real app, this would open a template creation dialog
                console.log('Create new template');
              }}
            >
              Nouveau template
            </Button>
          </Box>
          
          <List>
            {customTemplates.map((template) => (
              <React.Fragment key={template.id}>
                <ListItem>
                  <ListItemText
                    primary={template.name}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Type: {template.type === 'scanner' ? 'Scanner' : template.type === 'mri' ? 'IRM' : 'Échographie'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {template.description}
                        </Typography>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      aria-label="edit"
                      onClick={() => console.log('Edit template', template.id)}
                      sx={{ mr: 1 }}
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      edge="end"
                      aria-label="delete"
                      onClick={() => console.log('Delete template', template.id)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        </TabPanel>

        {/* Security Tab */}
        <TabPanel value={activeTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Changer le mot de passe
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      fullWidth
                      type="password"
                      label="Mot de passe actuel"
                    />
                    <TextField
                      fullWidth
                      type="password"
                      label="Nouveau mot de passe"
                    />
                    <TextField
                      fullWidth
                      type="password"
                      label="Confirmer le nouveau mot de passe"
                    />
                    <Button variant="contained" sx={{ alignSelf: 'flex-start' }}>
                      Changer le mot de passe
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Sessions actives
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="Session actuelle"
                        secondary="Navigateur Chrome - Aujourd'hui à 14:30"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Session mobile"
                        secondary="Application mobile - Hier à 09:15"
                      />
                      <ListItemSecondaryAction>
                        <Button size="small" color="error">
                          Déconnecter
                        </Button>
                      </ListItemSecondaryAction>
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default UserProfile;